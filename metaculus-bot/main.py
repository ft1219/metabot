import argparse
import asyncio
import atexit
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Literal

import dotenv

# Runtime helpers (env validation, banners, dependency-warning suppression).
import claude_month
from budget import BudgetedLlm, RunBudget
from claude_api import ClaudeApiLlm, ClaudeApiStatus
from openai_credit import OpenAiParserLlm, OpenAiStatus, parser_status
from web_search import ChatGptWebSearch, WebSearchResult, failure_annotation
from bot_config import (
    BotSettings,
    apply_monthly_claude_limit,
    uses_monthly_claude_limit,
    batch_size_for_money,
    batch_size_on_claude_api,
    load_settings,
    openrouter_twin,
    parser_kwargs,
    pick_questions_to_forecast,
    forecaster_kwargs,
)
from bot_helpers import (
    check_environment,
    announce_openrouter_money,
    drop_blank_env_vars,
    openrouter_money_left,
    print_run_summary_banner,
    print_startup_banner,
    silence_noisy_dependencies,
)

silence_noisy_dependencies()
# GitHub passes secrets that were never created as empty strings. An empty
# ASKNEWS_API_KEY would make the AskNews SDK send a blank key instead of using
# the client ID and secret, so blanks are removed before anything reads them.
drop_blank_env_vars()

from forecasting_tools import (
    AskNewsSearcher,
    BinaryQuestion,
    ForecastBot,
    GeneralLlm,
    MetaculusClient,
    MetaculusQuestion,
    MultipleChoiceQuestion,
    NumericDistribution,
    NumericQuestion,
    DateQuestion,
    DatePercentile,
    Percentile,
    ConditionalQuestion,
    ConditionalPrediction,
    PredictionTypes,
    PredictionAffirmed,
    BinaryPrediction,
    PredictedOptionList,
    ReasonedPrediction,
    SmartSearcher,
    clean_indents,
    structure_output,
)

dotenv.load_dotenv()
logger = logging.getLogger(__name__)


class FallTemplateBot2026(ForecastBot):
    """
    This is the template bot for the Fall 2026 FutureEval Bot Tournament.
    This is a copy of what is used by Metaculus to run the Metac Bots in our benchmark, provided as a template for new bot makers.
    This template is given as-is, and is use-at-your-own-risk.
    We have covered most test cases in forecasting-tools it may be worth double checking key components locally.
    So far our track record has been 1 mentionable bug per season (affecting forecasts for 1-2% of total questions)

    This bot is identical to SummerTemplateBot2026.

    The main entry point of this bot is `bot.forecast_on_tournament(tournament_id)` in the parent class.
    See the script at the bottom of the file for more details on how to run the bot.
    Ignoring the finer details, the general flow is:
    - Load questions from Metaculus
    - For each question
        - Execute run_research a number of times equal to research_reports_per_question
        - Execute respective run_forecast function `predictions_per_research_report * research_reports_per_question` times
        - Aggregate the predictions
        - Submit prediction (if publish_reports_to_metaculus is True)
    - Return a list of ForecastReport objects

    Alternatively, you can use the MetaculusClient to make a custom filter of questions to forecast on
    and forecast them with `bot.forecast_questions(questions)`

    Only the research and forecast functions need to be implemented in ForecastBot subclasses,
    though you may want to override other ForecastBot functions.
    In this example, you can change the prompts to be whatever you want since,
    structure_output uses an LLM to intelligently reformat the output into the needed structure.

    By default (i.e. 'tournament' mode), when you run this script, it will forecast on any open questions in the
    primary bot tournament and MiniBench. If you want to forecast on only one or the other, you can remove one
    of them from the 'tournament' mode code at the bottom of the file.

    You can experiment with what models work best with your bot by using the `llms` parameter when initializing the bot.
    You can initialize the bot with any number of models. For example,
    ```python
    my_bot = MyBot(
        ...
        llms={  # choose your model names or GeneralLlm llms here, otherwise defaults will be chosen for you
            "default": GeneralLlm(
                model="openrouter/openai/gpt-4o", # "anthropic/claude-sonnet-4-20250514", etc (see docs for litellm)
                temperature=0.3,
                timeout=40,
                allowed_tries=2,
            ),
            "summarizer": "openai/gpt-4o-mini",
            "researcher": "asknews/news-summaries",
            "parser": "openai/gpt-4o-mini",
        },
    )
    ```

    Then you can access the model in custom functions like this:
    ```python
    research_strategy = self.get_llm("researcher", "model_name")
    if research_strategy == "asknews/news-summaries":
        ...
    # OR
    summarizer = await self.get_llm("summarizer", "llm").invoke(prompt)
    # OR
    reasoning = await self.get_llm("default", "llm").invoke(prompt)
    ```

    If you end up having trouble with rate limits and want to try a more sophisticated rate limiter try:
    ```python
    from forecasting_tools import RefreshingBucketRateLimiter
    rate_limiter = RefreshingBucketRateLimiter(
        capacity=2,
        refresh_rate=1,
    ) # Allows 1 request per second on average with a burst of 2 requests initially. Set this as a class variable
    await self.rate_limiter.wait_till_able_to_acquire_resources(1) # 1 because it's consuming 1 request (use more if you are adding a token limit)
    ```
    Additionally OpenRouter has large rate limits immediately on account creation
    """

    _max_concurrent_questions = (
        1  # Set this to whatever works for your search-provider/ai-model rate limits
    )
    _concurrency_limiter = asyncio.Semaphore(_max_concurrent_questions)
    _structure_output_validation_samples = 2
    # ChatGPT web search, the second news source (make_bot sets it when
    # OPENAI_API_KEY is saved); None leaves the researcher alone.
    web_search: ChatGptWebSearch | None = None

    ##################################### RESEARCH #####################################

    async def run_research(self, question: MetaculusQuestion) -> str:
        """
        The researcher's news (AskNews) and ChatGPT web search's, fetched at
        the same time and put together. The web search runs outside the
        limiter that makes AskNews searches wait their turn, so web searches
        never queue behind each other or behind AskNews; a question's research
        takes as long as the slower of the two (the web search's timeout caps
        it). A question goes ahead with whichever source
        answered, and fails only when no source did: a forecast made without
        any news scores badly, and the next run tries it again.
        """
        researcher = self.get_llm("researcher")
        web_search = self.web_search
        (found, failure), searched = await asyncio.gather(
            self._research_with_researcher(question, researcher),
            web_search.search(question) if web_search else _no_web_search(),
        )
        research = self._put_research_together(question, researcher, found, failure, searched)
        logger.info(f"Found Research for URL {question.page_url}:\n{research}")
        return research

    @staticmethod
    def _researcher_name(researcher: str | GeneralLlm) -> str:
        name = GeneralLlm.to_model_name(researcher) if researcher else ""
        return "AskNews" if name.startswith("asknews/") else name

    def _put_research_together(
        self,
        question: MetaculusQuestion,
        researcher: str | GeneralLlm,
        found: str | None,
        failure: Exception | None,
        searched: WebSearchResult | None,
    ) -> str:
        """
        One research text: the researcher's part first, then the web search's
        under a heading with its date. With no web search part it is the
        researcher's text exactly as before.
        """
        name = self._researcher_name(researcher)
        uses_researcher = not _no_researcher(researcher)
        web_text = searched.text if searched else None
        if searched is not None:
            if found:
                instead = f"Forecast with {name} news only"
            elif failure is not None or not uses_researcher:
                instead = "No other news came through, so this question is not forecast this run"
            else:
                instead = "Forecast without news"
            note = failure_annotation(question.page_url, searched, self.web_search.status, instead)
            if note:
                # print, not the logger: a GitHub annotation must start the line.
                print(note, flush=True)
        if not found and not web_text:
            if failure is not None and searched is not None and searched.why:
                raise RuntimeError(
                    f"No news for {question.page_url}: {name} failed ({type(failure).__name__}: "
                    f"{failure}) and ChatGPT web search failed ({searched.why})"
                ) from failure
            if failure is not None:
                raise failure
            if searched is not None and not uses_researcher:
                raise RuntimeError(
                    f"No news for {question.page_url}: ChatGPT web search "
                    + (f"failed ({searched.why})" if searched.why else f"was not run ({searched.skipped})")
                    + " and no other researcher is set"
                )
            return found or ""
        if not web_text:
            return found
        web_part = f"## News from ChatGPT web search (searched {searched.searched_on} UTC)\n{web_text}"
        if failure is not None:
            logger.warning(
                f"{name} failed for {question.page_url} ({type(failure).__name__}: {failure}); "
                "forecasting with ChatGPT web search news only."
            )
            self.web_search.covered_for[type(failure).__name__] += 1
        if not found:
            return web_part
        return f"## News from {name}\n{found.strip()}\n\n{web_part}"

    async def _research_with_researcher(
        self, question: MetaculusQuestion, researcher: str | GeneralLlm
    ) -> tuple[str | None, Exception | None]:
        """(the researcher's text, None), or (None, the error it raised)."""
        try:
            return await self._run_researcher(question, researcher), None
        except Exception as e:
            logger.warning(f"Research for {question.page_url} failed: {type(e).__name__}: {e}")
            return None, e

    async def _run_researcher(self, question: MetaculusQuestion, researcher: str | GeneralLlm) -> str:
        async with self._concurrency_limiter:
            research = ""

            prompt = self._get_research_prompt(question, researcher)

            if isinstance(researcher, GeneralLlm):
                research = await researcher.invoke(prompt)
            elif (
                researcher == "asknews/news-summaries"
                or researcher == "asknews/deep-research/low-depth"
                or researcher == "asknews/deep-research/medium-depth"
                or researcher == "asknews/deep-research/high-depth"
            ):
                research = await AskNewsSearcher().call_preconfigured_version(
                    researcher, prompt
                )
            elif researcher.startswith("smart-searcher"):
                model_name = researcher.removeprefix("smart-searcher/")
                searcher = SmartSearcher(
                    model=model_name,
                    temperature=0,
                    num_searches_to_run=2,
                    num_sites_per_search=10,
                    use_advanced_filters=False,
                )
                research = await searcher.invoke(prompt)
            elif _no_researcher(researcher):
                research = ""
            else:
                research = await self.get_llm("researcher", "llm").invoke(prompt)
            return research

    @staticmethod
    def _get_research_prompt(
        question: MetaculusQuestion, researcher: str | GeneralLlm
    ) -> str:
        if GeneralLlm.to_model_name(researcher) == "asknews/news-summaries":
            return question.question_text

        prompt = clean_indents(
            f"""
            You are an assistant to a superforecaster.
            The superforecaster will give you a question they intend to forecast on.
            To be a great assistant, you generate a concise but detailed rundown of the most relevant news, including if the question would resolve Yes or No based on current information.
            You do not produce forecasts yourself.

            Question:
            {question.question_text}

            This question's outcome will be determined by the specific criteria below:
            {question.resolution_criteria}

            {question.fine_print}
            """
        )
        return prompt

    ##################################### BINARY QUESTIONS #####################################

    async def _run_forecast_on_binary(
        self, question: BinaryQuestion, research: str
    ) -> ReasonedPrediction[float]:
        prompt = clean_indents(
            f"""
            You are a professional forecaster interviewing for a job.

            Your interview question is:
            {question.question_text}

            Question background:
            {question.background_info}


            This question's outcome will be determined by the specific criteria below. These criteria have not yet been satisfied:
            {question.resolution_criteria}

            {question.fine_print}


            Your research assistant says:
            {research}

            Today is {datetime.now().strftime("%Y-%m-%d")}.

            Before answering you write:
            (a) The time left until the outcome to the question is known.
            (b) The status quo outcome if nothing changed.
            (c) A brief description of a scenario that results in a No outcome.
            (d) A brief description of a scenario that results in a Yes outcome.

            You write your rationale remembering that good forecasters put extra weight on the status quo outcome since the world changes slowly most of the time.
            {self._get_conditional_disclaimer_if_necessary(question)}

            The last thing you write is your final answer as: "Probability: ZZ%", 0-100
            """
        )

        return await self._binary_prompt_to_forecast(question, prompt)

    async def _binary_prompt_to_forecast(
        self,
        question: BinaryQuestion,
        prompt: str,
    ) -> ReasonedPrediction[float]:
        reasoning = await self.get_llm("default", "llm").invoke(prompt)
        logger.info(f"Reasoning for URL {question.page_url}: {reasoning}")
        parsing_instructions = clean_indents(
            f"""
            The text given to you is trying to give a probability forecast for a binary question.
            {self._create_resolved_question_parsing_message()}
            """
        )
        binary_prediction: BinaryPrediction = await structure_output(
            reasoning,
            BinaryPrediction,
            model=self.get_llm("parser", "llm"),
            num_validation_samples=self._structure_output_validation_samples,
            additional_instructions=parsing_instructions,
        )
        decimal_pred = max(0.01, min(0.99, binary_prediction.prediction_in_decimal))

        logger.info(
            f"Forecasted URL {question.page_url} with prediction: {decimal_pred}."
        )
        return ReasonedPrediction(prediction_value=decimal_pred, reasoning=reasoning)

    ##################################### MULTIPLE CHOICE QUESTIONS #####################################

    async def _run_forecast_on_multiple_choice(
        self, question: MultipleChoiceQuestion, research: str
    ) -> ReasonedPrediction[PredictedOptionList]:
        prompt = clean_indents(
            f"""
            You are a professional forecaster interviewing for a job.

            Your interview question is:
            {question.question_text}

            The options are: {question.options}


            Background:
            {question.background_info}

            {question.resolution_criteria}

            {question.fine_print}


            Your research assistant says:
            {research}

            Today is {datetime.now().strftime("%Y-%m-%d")}.

            Before answering you write:
            (a) The time left until the outcome to the question is known.
            (b) The status quo outcome if nothing changed.
            (c) A description of a scenario that results in an unexpected outcome.

            {self._get_conditional_disclaimer_if_necessary(question)}
            You write your rationale remembering that (1) good forecasters put extra weight on the status quo outcome since the world changes slowly most of the time, and (2) good forecasters leave some moderate probability on most options to account for unexpected outcomes.

            The last thing you write is your final probabilities for the N options in this order {question.options} as:
            Option_A: Probability_A
            Option_B: Probability_B
            ...
            Option_N: Probability_N
            """
        )
        return await self._multiple_choice_prompt_to_forecast(question, prompt)

    async def _multiple_choice_prompt_to_forecast(
        self,
        question: MultipleChoiceQuestion,
        prompt: str,
    ) -> ReasonedPrediction[PredictedOptionList]:
        parsing_instructions = clean_indents(
            f"""
            Make sure that all option names are one of the following:
            {question.options}

            The text you are parsing may prepend these options with some variation of "Option" which you should remove if not part of the option names I just gave you.
            Additionally, you may sometimes need to parse a 0% probability. Please do not skip options with 0% but rather make it an entry in your final list with 0% probability.
            {self._create_resolved_question_parsing_message()}
            """
        )
        reasoning = await self.get_llm("default", "llm").invoke(prompt)
        logger.info(f"Reasoning for URL {question.page_url}: {reasoning}")
        predicted_option_list: PredictedOptionList = await structure_output(
            text_to_structure=reasoning,
            output_type=PredictedOptionList,
            model=self.get_llm("parser", "llm"),
            num_validation_samples=self._structure_output_validation_samples,
            additional_instructions=parsing_instructions,
        )

        logger.info(
            f"Forecasted URL {question.page_url} with prediction: {predicted_option_list}."
        )
        return ReasonedPrediction(
            prediction_value=predicted_option_list, reasoning=reasoning
        )

    ##################################### NUMERIC QUESTIONS #####################################

    async def _run_forecast_on_numeric(
        self, question: NumericQuestion, research: str
    ) -> ReasonedPrediction[NumericDistribution]:
        upper_bound_message, lower_bound_message = (
            self._create_upper_and_lower_bound_messages(question)
        )
        prompt = clean_indents(
            f"""
            You are a professional forecaster interviewing for a job.

            Your interview question is:
            {question.question_text}

            Background:
            {question.background_info}

            {question.resolution_criteria}

            {question.fine_print}

            Units for answer: {question.unit_of_measure if question.unit_of_measure else "Not stated (please infer this)"}

            Your research assistant says:
            {research}

            Today is {datetime.now().strftime("%Y-%m-%d")}.

            {lower_bound_message}
            {upper_bound_message}

            Formatting Instructions:
            - Please notice the units requested and give your answer in these units (e.g. whether you represent a number as 1,000,000 or 1 million).
            - Never use scientific notation.
            - Always start with a smaller number (more negative if negative) and then increase from there. The value for percentile 10 should always be less than the value for percentile 20, and so on.

            Before answering you write:
            (a) The time left until the outcome to the question is known.
            (b) The outcome if nothing changed.
            (c) The outcome if the current trend continued.
            (d) The expectations of experts and markets.
            (e) A brief description of an unexpected scenario that results in a low outcome.
            (f) A brief description of an unexpected scenario that results in a high outcome.

            {self._get_conditional_disclaimer_if_necessary(question)}
            You remind yourself that good forecasters are humble and set wide 90/10 confidence intervals to account for unknown unknowns.

            The last thing you write is your final answer as:
            "
            Percentile 10: XX (lowest number value)
            Percentile 20: XX
            Percentile 40: XX
            Percentile 60: XX
            Percentile 80: XX
            Percentile 90: XX (highest number value)
            "
            """
        )
        return await self._numeric_prompt_to_forecast(question, prompt)

    async def _numeric_prompt_to_forecast(
        self,
        question: NumericQuestion,
        prompt: str,
    ) -> ReasonedPrediction[NumericDistribution]:
        reasoning = await self.get_llm("default", "llm").invoke(prompt)
        logger.info(f"Reasoning for URL {question.page_url}: {reasoning}")
        parsing_instructions = clean_indents(
            f"""
            The text given to you is trying to give a forecast distribution for a numeric question.
            - This text is trying to answer the numeric question: "{question.question_text}".
            {self._create_single_distribution_parsing_message(question)}
            {self._create_resolved_question_parsing_message()}
            - When parsing the text, please make sure to give the values (the ones assigned to percentiles) in terms of the correct units.
            - The units for the forecast are: {question.unit_of_measure}
            - Your work will be shown publicly with these units stated verbatim after the numbers your parse.
            - As an example, someone else guessed that the answer will be between {question.lower_bound} {question.unit_of_measure} and {question.upper_bound} {question.unit_of_measure}, so the numbers parsed from an answer like this would be verbatim "{question.lower_bound}" and "{question.upper_bound}".
            - If the answer doesn't give the answer in the correct units, you should parse it in the right units. For instance if the answer gives numbers as $500,000,000 and units are "B $" then you should parse the answer as 0.5 (since $500,000,000 is $0.5 billion).
            - If percentiles are not explicitly given (e.g. only a single value is given) please don't return a parsed output, but rather indicate that the answer is not explicitly given in the text.
            - Turn any values that are in scientific notation into regular numbers.
            """
        )
        percentile_list: list[Percentile] = await structure_output(
            reasoning,
            list[Percentile],
            model=self.get_llm("parser", "llm"),
            additional_instructions=parsing_instructions,
            num_validation_samples=self._structure_output_validation_samples,
        )
        prediction = NumericDistribution.from_question(percentile_list, question)
        logger.info(
            f"Forecasted URL {question.page_url} with prediction: {prediction.declared_percentiles}."
        )
        return ReasonedPrediction(prediction_value=prediction, reasoning=reasoning)

    ##################################### DATE QUESTIONS #####################################

    async def _run_forecast_on_date(
        self, question: DateQuestion, research: str
    ) -> ReasonedPrediction[NumericDistribution]:
        upper_bound_message, lower_bound_message = (
            self._create_upper_and_lower_bound_messages(question)
        )
        prompt = clean_indents(
            f"""
            You are a professional forecaster interviewing for a job.

            Your interview question is:
            {question.question_text}

            Background:
            {question.background_info}

            {question.resolution_criteria}

            {question.fine_print}

            Your research assistant says:
            {research}

            Today is {datetime.now().strftime("%Y-%m-%d")}.

            {lower_bound_message}
            {upper_bound_message}

            Formatting Instructions:
            - This is a date question, and as such, the answer must be expressed in terms of dates.
            - The dates must be written in the format of YYYY-MM-DD. If hours matter, please append the date with the hour in UTC and military time: YYYY-MM-DDTHH:MM:SSZ. No other formatting is allowed.
            - Always start with a lower date chronologically and then increase from there.
            - Do NOT forget this. The dates must be written in chronological order starting at the earliest time at percentile 10 and increasing from there.

            Before answering you write:
            (a) The time left until the outcome to the question is known.
            (b) The outcome if nothing changed.
            (c) The outcome if the current trend continued.
            (d) The expectations of experts and markets.
            (e) A brief description of an unexpected scenario that results in a low outcome.
            (f) A brief description of an unexpected scenario that results in a high outcome.

            {self._get_conditional_disclaimer_if_necessary(question)}
            You remind yourself that good forecasters are humble and set wide 90/10 confidence intervals to account for unknown unknowns.

            The last thing you write is your final answer as:
            "
            Percentile 10: YYYY-MM-DD (oldest date)
            Percentile 20: YYYY-MM-DD
            Percentile 40: YYYY-MM-DD
            Percentile 60: YYYY-MM-DD
            Percentile 80: YYYY-MM-DD
            Percentile 90: YYYY-MM-DD (newest date)
            "
            """
        )
        forecast = await self._date_prompt_to_forecast(question, prompt)
        return forecast

    async def _date_prompt_to_forecast(
        self,
        question: DateQuestion,
        prompt: str,
    ) -> ReasonedPrediction[NumericDistribution]:
        reasoning = await self.get_llm("default", "llm").invoke(prompt)
        logger.info(f"Reasoning for URL {question.page_url}: {reasoning}")
        parsing_instructions = clean_indents(
            f"""
            The text given to you is trying to give a forecast distribution for a date question.
            - This text is trying to answer the question: "{question.question_text}".
            {self._create_single_distribution_parsing_message(question)}
            {self._create_resolved_question_parsing_message()}
            - As an example, someone else guessed that the answer will be between {question.lower_bound} and {question.upper_bound}, so the numbers parsed from an answer like this would be verbatim "{question.lower_bound}" and "{question.upper_bound}".
            - The output is given as dates/times please format it into a valid datetime parsable string. Assume midnight UTC if no hour is given.
            - If percentiles are not explicitly given (e.g. only a single value is given) please don't return a parsed output, but rather indicate that the answer is not explicitly given in the text.
            """
        )
        date_percentile_list: list[DatePercentile] = await structure_output(
            reasoning,
            list[DatePercentile],
            model=self.get_llm("parser", "llm"),
            additional_instructions=parsing_instructions,
            num_validation_samples=self._structure_output_validation_samples,
        )

        percentile_list = [
            Percentile(
                percentile=percentile.percentile,
                value=percentile.value.timestamp(),
            )
            for percentile in date_percentile_list
        ]
        prediction = NumericDistribution.from_question(percentile_list, question)
        logger.info(
            f"Forecasted URL {question.page_url} with prediction: {prediction.declared_percentiles}."
        )
        return ReasonedPrediction(prediction_value=prediction, reasoning=reasoning)

    def _create_resolved_question_parsing_message(self) -> str:
        return "- If the text concludes that the question has already resolved *in the past* (i.e. it treats the question as decided rather than something to forecast), please DO NOT return a parsed output, even if a final forecast is also given. Instead indicate that the answer is not explicitly given in the text.\n"

    def _create_single_distribution_parsing_message(
        self, question: NumericQuestion | DateQuestion
    ) -> str:
        message = (
            "- The text may contain multiple percentile distributions (e.g. forecasts for several related questions/entities, or intermediate drafts before a final answer). You must return exactly ONE distribution: the single final distribution that answers the question stated above.\n"
            "- Never merge or concatenate percentile lists that refer to different entities, options, or scenarios. Each percentile should appear at most once in your output.\n"
            "- If there are multiple final distributions and you cannot tell which one answers the question stated above, do not guess or combine them. Instead indicate that the answer is not explicitly given in the text."
        )
        if question.group_question_option is not None:
            message += (
                f'\n- This question is specifically about "{question.group_question_option}" (one subquestion within a group of related questions). '
                f'If the text gives distributions for multiple subjects, return only the distribution for "{question.group_question_option}".'
            )
        return message

    def _create_upper_and_lower_bound_messages(
        self, question: NumericQuestion | DateQuestion
    ) -> tuple[str, str]:
        if isinstance(question, NumericQuestion):
            if question.nominal_upper_bound is not None:
                upper_bound_number = question.nominal_upper_bound
            else:
                upper_bound_number = question.upper_bound
            if question.nominal_lower_bound is not None:
                lower_bound_number = question.nominal_lower_bound
            else:
                lower_bound_number = question.lower_bound
            unit_of_measure = question.unit_of_measure
        elif isinstance(question, DateQuestion):
            upper_bound_number = question.upper_bound.date().isoformat()
            lower_bound_number = question.lower_bound.date().isoformat()
            unit_of_measure = ""
        else:
            raise ValueError()

        if question.open_upper_bound:
            upper_bound_message = f"The question creator thinks the number is likely not higher than {upper_bound_number} {unit_of_measure}."
        else:
            upper_bound_message = f"The outcome can not be higher than {upper_bound_number} {unit_of_measure}."

        if question.open_lower_bound:
            lower_bound_message = f"The question creator thinks the number is likely not lower than {lower_bound_number} {unit_of_measure}."
        else:
            lower_bound_message = f"The outcome can not be lower than {lower_bound_number} {unit_of_measure}."
        return upper_bound_message, lower_bound_message

    ##################################### CONDITIONAL QUESTIONS #####################################

    async def _run_forecast_on_conditional(
        self, question: ConditionalQuestion, research: str
    ) -> ReasonedPrediction[ConditionalPrediction]:
        parent_info, full_research = await self._get_question_prediction_info(
            question.parent, research, "parent"
        )
        child_info, full_research = await self._get_question_prediction_info(
            question.child, research, "child"
        )
        yes_info, full_research = await self._get_question_prediction_info(
            question.question_yes, full_research, "yes"
        )
        no_info, full_research = await self._get_question_prediction_info(
            question.question_no, full_research, "no"
        )
        full_reasoning = clean_indents(
            f"""
            ## Parent Question Reasoning
            {parent_info.reasoning}
            ## Child Question Reasoning
            {child_info.reasoning}
            ## Yes Question Reasoning
            {yes_info.reasoning}
            ## No Question Reasoning
            {no_info.reasoning}
        """
        )
        full_prediction = ConditionalPrediction(
            parent=parent_info.prediction_value,  # type: ignore
            child=child_info.prediction_value,  # type: ignore
            prediction_yes=yes_info.prediction_value,  # type: ignore
            prediction_no=no_info.prediction_value,  # type: ignore
        )
        return ReasonedPrediction(
            reasoning=full_reasoning, prediction_value=full_prediction
        )

    async def _get_question_prediction_info(
        self, question: MetaculusQuestion, research: str, question_type: str
    ) -> tuple[ReasonedPrediction[PredictionTypes | PredictionAffirmed], str]:
        from forecasting_tools.data_models.data_organizer import DataOrganizer

        previous_forecasts = question.previous_forecasts
        if (
            question_type in ["parent", "child"]
            and previous_forecasts
            and question_type not in self.force_reforecast_in_conditional
        ):
            # TODO: add option to not affirm current parent/child forecasts, create new forecast
            previous_forecast = previous_forecasts[-1]
            current_utc_time = datetime.now(timezone.utc)
            if (
                previous_forecast.timestamp_end is None
                or previous_forecast.timestamp_end > current_utc_time
            ):
                pretty_value = DataOrganizer.get_readable_prediction(previous_forecast)  # type: ignore
                prediction = ReasonedPrediction(
                    prediction_value=PredictionAffirmed(),
                    reasoning=f"Already existing forecast reaffirmed at {pretty_value}.",
                )
                return (prediction, research)  # type: ignore
        info = await self._make_prediction(question, research)
        full_research = self._add_reasoning_to_research(research, info, question_type)
        return info, full_research  # type: ignore

    def _add_reasoning_to_research(
        self,
        research: str,
        reasoning: ReasonedPrediction[PredictionTypes],
        question_type: str,
    ) -> str:
        from forecasting_tools.data_models.data_organizer import DataOrganizer

        question_type = question_type.title()
        return clean_indents(
            f"""
            {research}
            ---
            ## {question_type} Question Information
            You have previously forecasted the {question_type} Question to the value: {DataOrganizer.get_readable_prediction(reasoning.prediction_value)}
            This is relevant information for your current forecast, but it is NOT your current forecast, but previous forecasting information that is relevant to your current forecast.
            The reasoning for the {question_type} Question was as such:
            ```
            {reasoning.reasoning}
            ```
            This is absolutely essential: do NOT use this reasoning to re-forecast the {question_type} question.
            """
        )

    def _get_conditional_disclaimer_if_necessary(
        self, question: MetaculusQuestion
    ) -> str:
        if question.conditional_type not in ["yes", "no"]:
            return ""
        return clean_indents(
            """
            As you are given a conditional question with a parent and child, you are to only forecast the **CHILD** question, given the parent question's resolution.
            You never re-forecast the parent question under any circumstances, but you use probabilistic reasoning, strongly considering the parent question's resolution, to forecast the child question.
            """
        )


async def _no_web_search() -> None:
    return None


def _no_researcher(researcher: str | GeneralLlm) -> bool:
    return not researcher or researcher in ("None", "no_research")


def build_forecaster(
    settings: BotSettings,
    budget: RunBudget,
    model: str,
    claude_api: ClaudeApiStatus | None = None,
) -> BudgetedLlm:
    """
    The model that writes the forecasts. A Claude API model ("anthropic/...")
    redoes the forecasts it cannot make on its OpenRouter version.
    """
    # The timeout caps a whole call, not a silence. DeepSeek V3.2 with
    # reasoning takes 1.5 to 3 minutes on OpenRouter's cheaper hosts, so 180 s
    # failed whole questions on 2026-10-19. Metaculus runs its own DeepSeek
    # V3.2 reasoning bot with 300 s.
    if model.startswith("anthropic/"):
        twin = openrouter_twin(model)
        return ClaudeApiLlm(
            model=model,
            budget=budget,
            timeout=300,
            status=claude_api or ClaudeApiStatus(),
            fallback=build_forecaster(settings, budget, twin) if twin else None,
            **forecaster_kwargs(settings, model),
        )
    return BudgetedLlm(
        model=model,
        budget=budget,
        timeout=300,
        allowed_tries=2,
        **forecaster_kwargs(settings, model),
    )


def build_parser(
    settings: BotSettings, budget: RunBudget, status: OpenAiStatus | None = None
) -> BudgetedLlm:
    """
    The parser, which turns each forecast's written answer into a number. On
    OpenAI (GPT-6 Luna, with an OPENAI_API_KEY) every parse it cannot make is
    redone on its OpenRouter fallback (settings.parser_fallback_model).
    """
    # The parser reads answers that were already paid for, so it keeps
    # working past the spending limit (the call limit still applies).
    shared = {"budget": budget, "enforce_spending_limit": False}
    model, fallback_model = settings.parser_model, settings.parser_fallback_model
    if not fallback_model:
        return BudgetedLlm(model=model, **shared, **parser_kwargs(model))
    return OpenAiParserLlm(
        model=model,
        status=status or parser_status(),
        fallback=BudgetedLlm(model=fallback_model, **shared, **parser_kwargs(fallback_model)),
        **shared,
        **parser_kwargs(model),
    )


def build_llms(
    settings: BotSettings,
    budget: RunBudget,
    forecast_model: str | None = None,
    claude_api: ClaudeApiStatus | None = None,
    parser: OpenAiStatus | None = None,
) -> dict[str, str | GeneralLlm]:
    forecast_model = forecast_model or settings.forecast_model
    # Never called (summaries are off, see make_bot); a GPT-6 model takes no temperature.
    summarizer_kwargs = parser_kwargs(settings.parser_model)
    if summarizer_kwargs.get("temperature") is not None:
        summarizer_kwargs["temperature"] = 0.3
    return {
        "default": build_forecaster(settings, budget, forecast_model, claude_api),
        "summarizer": BudgetedLlm(model=settings.parser_model, budget=budget, **summarizer_kwargs),
        "researcher": settings.researcher,
        "parser": build_parser(settings, budget, parser),
    }


def build_web_search(
    settings: BotSettings, budget: RunBudget, status: OpenAiStatus | None = None
) -> ChatGptWebSearch | None:
    """ChatGPT web search for the whole run, or None when it is off (no OPENAI_API_KEY, or WEB_SEARCH_MODEL=none)."""
    if not settings.web_search_model:
        return None
    return ChatGptWebSearch(settings.web_search_model, budget, status)


def make_bot(
    settings: BotSettings,
    budget: RunBudget,
    publish: bool,
    forecast_model: str | None = None,
    claude_api: ClaudeApiStatus | None = None,
    web_search: ChatGptWebSearch | None = None,
    parser: OpenAiStatus | None = None,
) -> FallTemplateBot2026:
    """`web_search` and `parser` are shared by both bots, so a used-up OpenAI
    credit stops each job once for the whole run."""
    bot = FallTemplateBot2026(
        research_reports_per_question=1,
        predictions_per_research_report=settings.predictions_per_question,
        use_research_summary_to_forecast=False,
        # The summary only decorates the published comment, yet all five
        # forecasts wait for it (128 s on one slow host on 2026-10-19).
        enable_summarize_research=False,
        publish_reports_to_metaculus=publish,
        folder_to_save_reports_to=None,
        skip_previously_forecasted_questions=True,
        extra_metadata_in_explanation=True,
        llms=build_llms(settings, budget, forecast_model, claude_api, parser),
    )
    bot.web_search = web_search
    return bot


def collect_questions(
    client: MetaculusClient, tournament_ids: list[int | str]
) -> tuple[list[MetaculusQuestion], list[Exception]]:
    """
    Fetch open questions from each tournament. One tournament failing to load
    (e.g. MiniBench between rounds) must not stop forecasts on the others.
    """
    questions: list[MetaculusQuestion] = []
    errors: list[Exception] = []
    for tournament_id in tournament_ids:
        try:
            questions.extend(client.get_all_open_questions_from_tournament(tournament_id))
        except Exception as e:
            logger.exception(f"Could not load questions from tournament {tournament_id}")
            errors.append(e)
    return questions, errors


def load_questions(
    client: MetaculusClient, run_mode: str
) -> tuple[list[MetaculusQuestion], list[MetaculusQuestion], list[Exception]]:
    """
    Returns (questions for the stronger model, questions for the cheaper
    model, load errors). The main tournament, where most of the prize money
    is, gets the stronger model; MiniBench and the Cup the cheaper one. The
    practice questions use the stronger one, so a test run checks that setup.
    """
    if run_mode == "tournament":
        strong, errors = collect_questions(client, [client.CURRENT_AI_COMPETITION_ID])
        cheap, more_errors = collect_questions(client, [client.CURRENT_MINIBENCH_ID])
        return strong, cheap, errors + more_errors
    if run_mode == "metaculus_cup":
        cheap, errors = collect_questions(client, [client.CURRENT_METACULUS_CUP_ID])
        return [], cheap, errors
    # The bot-testing-area tournament contains all question types and is the
    # recommended target for smoke-testing the bot.
    strong, errors = collect_questions(client, ["bot-testing-area"])
    return strong, [], errors


def models_to_call(
    settings: BotSettings,
    chosen_strong: list[MetaculusQuestion],
    chosen_cheap: list[MetaculusQuestion],
) -> list[str]:
    """The models this run will call for the questions it picked."""
    if not (chosen_strong or chosen_cheap):
        return []
    forecasters = []
    if chosen_strong:
        forecasters.append(settings.tournament_forecast_model)
    if chosen_cheap:
        forecasters.append(settings.forecast_model)
    # A Claude API forecaster's failed forecasts are redone on OpenRouter, and
    # so are the parses an OpenAI parser cannot make.
    twins = [twin for twin in map(openrouter_twin, forecasters) if twin]
    parser_fallback = [settings.parser_fallback_model] if settings.parser_fallback_model else []
    return [settings.parser_model] + parser_fallback + forecasters + twins


class OpenRouterGate:
    """
    Before each batch of questions, before its research is paid for, reads
    what the bot can still spend on OpenRouter and says how many questions
    fit at once. Questions that do not fit at all are held back for the next
    run. Reading again before every batch accounts for what earlier batches
    spent, and judging each group by its own model lets MiniBench on OpenAI
    run while Claude cannot.
    """

    def __init__(self, settings: BotSettings, read_money=None):
        self.settings = settings
        self.read_money = read_money or openrouter_money_left
        self.held_back: list[MetaculusQuestion] = []
        self.money_when_held = None
        self.lowest_money = None

    def batch_sizer(self, model):
        """`model`: the model whose forecasts OpenRouter pays for, or a function
        that turns the money left into a batch size (asked before every batch)."""

        def next_batch_size(remaining: list[MetaculusQuestion]) -> int:
            money = self.read_money()
            if money is not None and (self.lowest_money is None or money.left < self.lowest_money.left):
                self.lowest_money = money
            left = money.left if money else None
            size = model(left) if callable(model) else batch_size_for_money(self.settings, model, left)
            if size == 0:
                self.held_back.extend(remaining)
                self.money_when_held = self.money_when_held or money
            return size

        return next_batch_size

    def announce(self) -> None:
        announce_openrouter_money(self.money_when_held or self.lowest_money, len(self.held_back))


async def forecast_chosen(
    settings: BotSettings,
    tournament_bot: ForecastBot,
    other_bot: ForecastBot,
    chosen_strong: list[MetaculusQuestion],
    chosen_cheap: list[MetaculusQuestion],
    budget: RunBudget,
    read_money=None,
    claude_api: ClaudeApiStatus | None = None,
) -> tuple[list, list[MetaculusQuestion], list[MetaculusQuestion]]:
    """
    Forecast the main tournament questions, then MiniBench/Cup, within the
    run budget and the OpenRouter money left. Returns (reports, questions not
    attempted because the run budget ran out, questions held back for lack of
    OpenRouter money).
    """
    uses_openrouter = any(
        m.startswith("openrouter/")
        for m in models_to_call(settings, chosen_strong, chosen_cheap)
    )
    gate = OpenRouterGate(settings, read_money) if uses_openrouter else None

    def paid_on_openrouter(model: str):
        # The money rule for the Claude API. While it answers, a question on it
        # needs OpenRouter only for its parse calls (with the parser on OpenAI,
        # only for those OpenAI cannot make), so low OpenRouter money
        # does not hold it back. Until it has answered this run, and after a
        # batch in which some forecasts were redone on OpenRouter, the next
        # batch is sized for OpenRouter but always lets one question through
        # (bot_config.batch_size_on_claude_api). Once the Claude API is down
        # for the run (key, credit, access, repeated timeouts), every forecast
        # goes to OpenRouter, so the questions still waiting are judged by the
        # OpenRouter model, exactly as without the key.
        twin = openrouter_twin(model)
        if not twin or claude_api is None:
            return model
        redone_before = claude_api.redone

        def size_for(money_left: float | None) -> int:
            nonlocal redone_before
            proven = claude_api.answered > 0 and claude_api.redone == redone_before
            redone_before = claude_api.redone
            if claude_api.down_reason:
                return batch_size_for_money(settings, twin, money_left)
            return batch_size_on_claude_api(settings, model, money_left, proven)

        return size_for

    def sizer(model):
        return gate.batch_sizer(paid_on_openrouter(model)) if gate else None

    reports, not_attempted = await forecast_groups(
        [
            (tournament_bot, chosen_strong, sizer(settings.tournament_forecast_model)),
            (other_bot, chosen_cheap, sizer(settings.forecast_model)),
        ],
        settings.questions_in_parallel,
        budget,
    )
    if gate:
        gate.announce()
    return reports, not_attempted, (gate.held_back if gate else [])


def split_by_model(
    chosen: list[MetaculusQuestion], strong: list[MetaculusQuestion]
) -> tuple[list[MetaculusQuestion], list[MetaculusQuestion]]:
    """Split the questions picked for this run into (stronger model, cheaper model)."""
    strong_ids = {id(q) for q in strong}
    return (
        [q for q in chosen if id(q) in strong_ids],
        [q for q in chosen if id(q) not in strong_ids],
    )


async def forecast_in_batches(
    bot: ForecastBot,
    questions: list[MetaculusQuestion],
    batch_size: int,
    budget: RunBudget,
    next_batch_size=None,
) -> tuple[list, list[MetaculusQuestion]]:
    """
    Forecast `batch_size` questions at a time, stopping before the next batch
    once the run budget is spent. Returns (reports, questions not attempted).

    `next_batch_size(remaining questions)`, when given, decides each batch's
    size instead; 0 stops the group, and it keeps track of the questions left.
    """
    reports: list = []
    start = 0
    while start < len(questions):
        if budget.exhausted:
            return reports, list(questions[start:])
        size = batch_size if next_batch_size is None else next_batch_size(list(questions[start:]))
        if size <= 0:
            return reports, []
        batch = questions[start : start + size]
        reports.extend(await bot.forecast_questions(batch, return_exceptions=True))
        start += size
    return reports, []


async def forecast_groups(
    groups: list[tuple],
    batch_size: int,
    budget: RunBudget,
) -> tuple[list, list[MetaculusQuestion]]:
    """
    Forecast each (bot, questions) group in turn under one shared run budget,
    `batch_size` questions at a time. A group may carry a third item, a
    next_batch_size function for forecast_in_batches. Returns (reports,
    questions not attempted) across all groups.
    """
    reports: list = []
    not_attempted: list[MetaculusQuestion] = []
    for bot, questions, *sizer in groups:
        if not questions:
            continue
        done, skipped = await forecast_in_batches(
            bot, questions, batch_size, budget, sizer[0] if sizer else None
        )
        reports.extend(done)
        not_attempted.extend(skipped)
    return reports, not_attempted


def settings_for_this_month(settings: BotSettings, env=None) -> BotSettings:
    """
    Moves the main tournament from Fable to Sonnet once this credit month's
    Claude API spend reaches the monthly limit, or when it cannot be read.
    """
    if not uses_monthly_claude_limit(settings):
        return settings
    today = datetime.now(timezone.utc).date()
    reset_day = settings.claude_credit_reset_day
    try:
        spent = claude_month.read_month_spend(today, reset_day, env)
    except Exception as e:
        # Never let the count stop the forecasts; an unknown count means Sonnet.
        logger.warning(f"Could not read this month's Claude API spend: {e!r}")
        spent = None
    renews = claude_month.next_reset(today, reset_day)
    settings, note = apply_monthly_claude_limit(
        settings, spent, f"{renews.day} {renews:%B}"
    )
    if note:
        print(note, flush=True)
    return settings


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="Run the forecasting bot")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["tournament", "metaculus_cup", "test_questions"],
        default="tournament",
        help="What to forecast on (default: tournament)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Make forecasts but do not submit them to Metaculus",
    )
    args = parser.parse_args()
    run_mode: Literal["tournament", "metaculus_cup", "test_questions"] = args.mode

    settings = load_settings()
    check_environment(strict=True, researcher=settings.researcher)
    publish_to_metaculus = not args.dry_run
    print_startup_banner(run_mode, will_publish=publish_to_metaculus)
    settings = settings_for_this_month(settings)
    logger.info(f"Settings: {settings}")
    claude_api_key_saved = bool((os.getenv("ANTHROPIC_API_KEY") or "").strip())
    if claude_api_key_saved and not settings.tournament_forecast_model.startswith("anthropic/"):
        # The saved key would otherwise go unused without a word.
        print(
            f"::notice title=Claude API key not used::TOURNAMENT_FORECAST_MODEL is "
            f"{settings.tournament_forecast_model}, which has no Claude API version, so this run "
            "does not use ANTHROPIC_API_KEY. Leave the variable blank to use the Claude API credit."
        )
    budget = RunBudget(settings.max_cost_per_run_usd, settings.max_llm_calls_per_run)
    # What the Claude API did this run (used when ANTHROPIC_API_KEY is saved).
    claude_api = ClaudeApiStatus()
    # The Claude API credit the run used goes to the job's outputs, for the
    # job that adds it to this month's count, however the run ends (failed
    # questions exit with 1; an error ends it with a traceback).
    atexit.register(lambda: claude_month.write_run_output(claude_api.credit_used_usd()))

    # With OPENAI_API_KEY saved, ChatGPT web search (a second news source)
    # and the parser run on the free OpenAI credit; what they did this run.
    web_search = build_web_search(settings, budget)
    parser_on_openai = parser_status()

    # The main tournament gets the stronger model; MiniBench and the Cup keep
    # the cheaper one. Both share the run budget, the web search and the parser.
    tournament_bot = make_bot(
        settings,
        budget,
        publish=publish_to_metaculus,
        forecast_model=settings.tournament_forecast_model,
        claude_api=claude_api,
        web_search=web_search,
        parser=parser_on_openai,
    )
    other_bot = make_bot(
        settings,
        budget,
        publish=publish_to_metaculus,
        claude_api=claude_api,
        web_search=web_search,
        parser=parser_on_openai,
    )

    TOURNAMENT_URLS = {
        "tournament": "https://www.metaculus.com/tournament/fall-futureeval-2026/",
        "metaculus_cup": "https://www.metaculus.com/tournament/metaculus-cup-fall-2026/",
        "test_questions": "https://www.metaculus.com/tournament/bot-testing-area/",
    }

    client = MetaculusClient()
    strong_questions, cheap_questions, load_errors = load_questions(client, run_mode)
    open_questions = strong_questions + cheap_questions
    if run_mode != "tournament":
        # The Metaculus Cup may be uninitialized near the start of a season,
        # and practice questions are forecast again on every test run.
        tournament_bot.skip_previously_forecasted_questions = False
        other_bot.skip_previously_forecasted_questions = False
        for question in open_questions:
            question.already_forecasted = False
    chosen, deferred = pick_questions_to_forecast(
        open_questions, settings.max_questions_per_run
    )
    logger.info(
        f"{len(open_questions)} open questions, {len(chosen)} to forecast now, "
        f"{len(deferred)} deferred to the next run"
    )

    # Main tournament questions first: if the budget runs out, MiniBench waits.
    chosen_strong, chosen_cheap = split_by_model(chosen, strong_questions)
    # Questions OpenRouter would refuse wait for the next run, before their
    # research is paid for; the run then shows as failed (which emails the
    # owner) and its page says why.
    forecast_reports, not_attempted, held_back = asyncio.run(
        forecast_chosen(
            settings,
            tournament_bot,
            other_bot,
            chosen_strong,
            chosen_cheap,
            budget,
            claude_api=claude_api,
        )
    )

    if forecast_reports or not held_back:
        # raise_errors=False so the summary lines below still print when a
        # question failed; the exit code at the end reports the failure.
        tournament_bot.log_report_summary(forecast_reports, raise_errors=False)
        print_run_summary_banner(
            forecast_reports,
            will_publish=publish_to_metaculus,
            tournament_url=TOURNAMENT_URLS.get(run_mode),
        )
    print(f"💰  {budget.cost_line()}")
    credit_used = claude_api.credit_used_usd()
    if credit_used:
        # What goes into this month's count: also replies that were charged
        # but gave no forecast (refusals, answers cut off, timeouts).
        print(f"🧮  Claude API credit counted toward this month: ${credit_used:.4f}")
    # The Claude API being down, or some forecasts redone on OpenRouter, shows
    # as a warning on the run's page; the run still passes if they worked.
    claude_api_note = claude_api.annotation()
    if claude_api_note:
        print(claude_api_note)
    if web_search:
        print(f"🔎  {web_search.summary()}")
    # Parses redone on OpenRouter, and questions ChatGPT web search carried
    # alone because AskNews failed, show as warnings on the run's page.
    for note in (parser_on_openai.annotation(), web_search.covered_annotation() if web_search else None):
        if note:
            print(note)
    if budget.calls_without_cost:
        print(
            f"⚠️   {budget.calls_without_cost} call(s) had no price; the cost above is too low."
        )
    if budget.failed_calls:
        print(
            f"⚠️   {budget.failed_calls} call(s) failed after being sent; any cost they "
            "had is not in the total above."
        )
    if budget.estimated_calls:
        print(
            f"⚠️   {budget.estimated_calls} call(s) were cut off before their answer came back; "
            "the total above counts each at the most it is likely to have cost."
        )
    if not_attempted:
        print(
            f"🛑  Run budget used up; {len(not_attempted)} question(s) not attempted. "
            "They will be tried on the next run."
        )
    if deferred:
        print(f"⏭️   {len(deferred)} question(s) left for the next run.")
    if held_back:
        print(
            f"💳  {len(held_back)} question(s) not forecast: too little OpenRouter "
            "money left. They will be tried on the next run."
        )

    # A failed question makes the GitHub Actions run show as failed, which
    # emails the repository owner. The next run retries it automatically.
    failures = [r for r in forecast_reports if isinstance(r, BaseException)]
    if failures or load_errors or not_attempted or held_back:
        sys.exit(1)

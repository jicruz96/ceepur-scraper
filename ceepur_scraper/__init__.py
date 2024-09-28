import asyncio
import csv
import os
from argparse import ArgumentParser
from typing import Any

import aiohttp
from random_user_agent.params import OperatingSystem, SoftwareName  # type: ignore
from random_user_agent.user_agent import UserAgent  # type: ignore
from tqdm import tqdm

from ceepur_scraper.csv_writer import CSVWriter, IncompatibleColumnNamesError
from ceepur_scraper.models import PublicVoterRecord

CEEPUR_VOTER_INFO_URL: str = "https://consulta.ceepur.org/ElectorService.asmx/ConsultaElectorById"


class PuertoRicoVoterRecordScraper:
    """Utility for scraping the Puerto Rico voter registry."""

    def __init__(
        self,
        output_filename: str,
        max_id: int = 9_999_999,
        min_id: int = 1,
        reverse: bool = False,
        max_concurrent_tasks: int = 15_000,
        save_descriptions: bool = False,
        continue_previous_scrape: bool = False,
        debug: bool = False,
    ):
        if os.path.exists(output_filename) and not continue_previous_scrape:
            print(
                f"\nERROR: There already exists a file named {output_filename!r}.\n\n"
                "If you intend to continue a previous scrape that was interrupted, use the -c/--continue-previous-scrape flag.\n"
                "Otherwise, either delete the existing file or use the -o/--output flag to specify a new output file.\n"
            )
            exit(1)
        self.output_filename = output_filename
        self.max_id = max_id
        self.min_id = min_id
        self.reverse = reverse
        self.max_concurrent_tasks = max_concurrent_tasks
        self.save_descriptions = save_descriptions
        self.continue_previous_scrape = continue_previous_scrape
        self.debug = debug
        if self.max_id > 9_999_999:
            raise ValueError("max_id must be less than 9,999,999")
        if self.min_id < 1:
            raise ValueError("min_id must be greater than 0")
        if self.min_id > self.max_id:
            raise ValueError("min_id must be less than or equal to max_id")
        columns = [
            "NumeroElectoral",
            "Category",
            "FechaNacimiento",
            "Precinto",
            "Status",
            "Unidad",
        ]
        if self.save_descriptions:
            columns.extend(["EstatusDescripcion", "CategoriaDescripcion"])
        self.user_agent_rotator = UserAgent(
            software_names=[enum.value for enum in SoftwareName],
            operating_systems=[enum.value for enum in OperatingSystem],
            limit=1000,
        )
        try:
            self.output_writer = CSVWriter(
                filename=self.output_filename,
                columns=columns,
                buffer_size=1_000,
            )
        except IncompatibleColumnNamesError:
            print(
                f"\nERROR: Cannot continue scrape because the output file {self.output_filename!r} "
                f"has different columns than expected.\n"
                f"Expected columns: {columns}\n"
                "Please delete the file and try again.\n"
            )
            exit(1)

    @property
    def random_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/xml, text/xml, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.7",
            "Connection": "keep-alive",
            "Host": "consulta.ceepur.org",
            "Origin": "https://consulta.ceepur.org",
            "Referer": "https://consulta.ceepur.org/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": self.user_agent_rotator.get_random_user_agent(),
        }

    async def scrape(self):
        voter_ids_to_scrape = list(range(self.min_id, self.max_id + 1))
        if self.reverse:
            voter_ids_to_scrape = list(reversed(voter_ids_to_scrape))

        if self.continue_previous_scrape and os.path.exists(self.output_filename):
            voter_ids_to_scrape = list(
                set(voter_ids_to_scrape).difference(
                    [
                        int(row["NumeroElectoral"])
                        for row in csv.DictReader(open(self.output_filename, "r", newline="", encoding="utf-8"))
                    ]
                )
            )
        tasks: set[asyncio.Task[Any]] = set()
        try:
            with tqdm(total=len(voter_ids_to_scrape)) as progress_bar:
                async with aiohttp.ClientSession() as session:
                    while len(voter_ids_to_scrape) > 0 or len(tasks) > 0:
                        while len(voter_ids_to_scrape) > 0 and len(tasks) < self.max_concurrent_tasks:
                            tasks.add(
                                asyncio.create_task(
                                    self.get_voter_record_from_ceepur(
                                        voter_id=voter_ids_to_scrape.pop(0),
                                        session=session,
                                    )
                                )
                            )
                        completed, tasks = await asyncio.wait(
                            tasks,
                            return_when=asyncio.FIRST_COMPLETED,
                            timeout=5.0,
                        )
                        # if any tasks errored, we'll just let the exception propagate
                        # and let the caller handle it
                        failed = [task for task in completed if task.exception() is not None]
                        if len(failed) > 0:
                            exc = failed[0].exception()
                            assert isinstance(exc, BaseException)
                            raise exc
                        progress_bar.update(len(completed))
        except KeyboardInterrupt:
            print(
                "\nWARNING: The scrape was interrupted before it finished.\n\n"
                "TIPS:\n"
                "  * Re-run the scraper with -c/--continue-previous-scrape to attempt to resume the scrape.\n"
            )
        except Exception:
            print(
                "\nWARNING: The scrape encountered an unknwon error before it finished.\n\n"
                "TIPS:\n\n"
                "  * Re-run the scraper with -c/--continue-previous-scrape to attempt to resume the scrape.\n"
                "  * Re-run the scraper with -d/--debug to see the full error message.\n"
            )
            if self.debug:
                raise
            exit(1)
        finally:
            for task in tasks:
                task.cancel()
            self.output_writer.flush()

    async def get_voter_record_from_ceepur(self, voter_id: int, session: aiohttp.ClientSession) -> None:
        async with session.post(
            CEEPUR_VOTER_INFO_URL,
            data={"numeroElectoral": voter_id},
            headers=self.random_headers,
        ) as response:
            record = await PublicVoterRecord.parse_ceepur_api_response(response)
            if record:
                row = {
                    "NumeroElectoral": str(record.NumeroElectoral),
                    "Category": record.Category,
                    "FechaNacimiento": record.FechaNacimiento,
                    "Precinto": str(record.Precinto),
                    "Status": record.Status,
                    "Unidad": str(record.Unidad),
                }
                if self.save_descriptions:
                    row.update(
                        {
                            "EstatusDescripcion": record.EstatusDescripcion,
                            "CategoriaDescripcion": record.CategoriaDescripcion,
                        }
                    )
                self.output_writer.dict_write_row(row)

    @classmethod
    def cli(cls) -> None:
        parser = ArgumentParser()
        parser.add_argument(
            "--output",
            "-o",
            dest="output_filename",
            default="voter_records.csv",
            help="The filename to write the scraped voter records to. Defaults to voter_records.csv.",
        )
        parser.add_argument(
            "--max-id",
            dest="max_id",
            default=9_999_999,
            type=int,
            help="The maximum voter ID to scrape. Cannot be greater than 9,999,999.",
        )
        parser.add_argument(
            "--min-id",
            default=1,
            type=int,
            help="The minimum voter ID to scrape. Cannot be less than 1.",
        )
        parser.add_argument(
            "--reverse",
            action="store_true",
            help="Whether to scrape in reverse order.",
        )
        parser.add_argument(
            "--max-concurrent-tasks",
            default=500,
            type=int,
            help="The maximum number of concurrent tasks to run. Defaults to 500.",
        )
        parser.add_argument(
            "--continue-previous-scrape",
            "-c",
            action="store_true",
            help="Whether to continue a previous scrape that was interrupted.",
        )
        parser.add_argument(
            "--save-descriptions",
            action="store_true",
            help=(
                "Whether to save the descriptions of the voter's status and category. "
                "⚠️ WARNING: This will significantly increase the size of the output file."
            ),
        )
        parser.add_argument(
            "--debug",
            "-d",
            action="store_true",
            help="Run in debug mode.",
        )
        asyncio.run(cls(**vars(parser.parse_args())).scrape())


def main() -> None:
    PuertoRicoVoterRecordScraper.cli()


if __name__ == "__main__":
    main()

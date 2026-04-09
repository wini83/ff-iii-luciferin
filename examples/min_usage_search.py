"""Demonstrate minimal usage of :class:`FireflyClient`. fetching transactions."""

import asyncio
import logging

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text
from settings_min import settings

from ff_iii_luciferin.api import FireflyClient
from ff_iii_luciferin.domain.formatters import format_amount
from ff_iii_luciferin.domain.models import SimplifiedAccountRef

logging.basicConfig(level=logging.INFO)
console = Console()


def format_account(account: SimplifiedAccountRef | None) -> str:
    if account is None:
        return "-"

    iban = f" [{account.iban[-4:]}]" if account.iban else ""
    return f"{account.name} ({account.type}){iban}"


def format_amount_cell(amount: str) -> Text:
    style = "green" if not amount.startswith("-") else "red"
    return Text(amount, style=style)


def build_transactions_table() -> Table:
    table = Table(
        title="Recent Transactions",
        caption="Showing first 20 rows",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
        border_style="bright_black",
        title_style="bold white",
        caption_style="dim",
        # row_styles=["none", "dim"],
        expand=False,
    )
    table.add_column("ID", justify="right", no_wrap=True, style="bold")
    table.add_column("Date", no_wrap=True, style="bright_black")
    table.add_column("Amt", justify="right", no_wrap=True)
    table.add_column("Desc", max_width=28, overflow="ellipsis")
    table.add_column("Cat", max_width=16, overflow="ellipsis", style="magenta")
    table.add_column("From", max_width=24, overflow="ellipsis", style="cyan")
    table.add_column("To", max_width=24, overflow="ellipsis", style="yellow")
    return table


async def main() -> None:
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        transactions = await firefly.fetch_transactions(max_pages=1)
        logging.info("Fetched %s transactions", len(transactions))
        table = build_transactions_table()
        for tx in transactions[:20]:
            amount = (
                f"{format_amount(tx.amount, tx.currency.decimals)} {tx.currency.symbol}"
            )
            table.add_row(
                str(tx.id),
                tx.date.isoformat(),
                format_amount_cell(amount),
                tx.description,
                tx.category.name if tx.category else "-",
                format_account(tx.source_account),
                format_account(tx.destination_account),
            )
        console.print(table)
    finally:
        await firefly.close()
    uncategorized = [tx for tx in transactions if tx.category is None]
    logging.info("Found %s uncategorized transactions", len(uncategorized))


asyncio.run(main())

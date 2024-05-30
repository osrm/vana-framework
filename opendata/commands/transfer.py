# The MIT License (MIT)
# Copyright © 2024 Corsali, Inc. dba Vana

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import argparse
import sys

from rich.prompt import Prompt

import opendata
from . import defaults

console = opendata.__console__


class TransferCommand:
    """
    Executes the ``transfer`` command to transfer DAT tokens from one account to another on the Vana network.

    This command is used for transactions between different accounts, enabling users to send tokens to other participants on the network.

    Usage:
        The command requires specifying the destination address (public key) and the amount of DAT to be transferred.
        It checks for sufficient balance and prompts for confirmation before proceeding with the transaction.

    Optional arguments:
        - ``--dest`` (str): The destination address for the transfer. This can be in the form of an h160 or secp256k1 public key.
        - ``--amount`` (float): The amount of DAT tokens to transfer.

    The command displays the user's current balance before prompting for the amount to transfer, ensuring transparency and accuracy in the transaction.

    Example usage::

        vanacli wallet transfer --dest 5Dp8... --amount 100

    Note:
        This command is crucial for executing token transfers within the Vana network. Users should verify the destination address and amount before confirming the transaction to avoid errors or loss of funds.
    """

    @staticmethod
    def run(cli: "opendata.cli"):
        r"""Transfer token of amount to destination."""
        try:
            chain_manager: "opendata.ChainManager" = opendata.ChainManager(
                config=cli.config
            )
            TransferCommand._run(cli, chain_manager)
        finally:
            if "chain_manager" in locals():
                chain_manager.close()
                opendata.logging.debug("closing chain_manager connection")

    @staticmethod
    def _run(cli: "opendata.cli", chain_manager: "opendata.ChainManager"):
        r"""Transfer token of amount to destination."""
        wallet = opendata.Wallet(config=cli.config)
        chain_manager.transfer(
            wallet=wallet,
            dest=cli.config.dest,
            amount=cli.config.amount,
            wait_for_inclusion=True,
            prompt=not cli.config.no_prompt,
        )

    @staticmethod
    def check_config(config: "opendata.Config"):
        if not config.is_set("wallet.name") and not config.no_prompt:
            wallet_name = Prompt.ask("Enter wallet name", default=defaults.wallet.name)
            config.wallet.name = str(wallet_name)

        # Get destination.
        if not config.dest and not config.no_prompt:
            dest = Prompt.ask("Enter destination public key: (h160 or secp256k1)")
            if not opendata.utils.is_valid_opendata_address_or_public_key(dest):
                sys.exit()
            else:
                config.dest = str(dest)

        # Get current balance and print to user.
        if not config.no_prompt:
            wallet = opendata.Wallet(config=config)
            chain_manager = opendata.ChainManager(config=config)
            with opendata.__console__.status(":satellite: Checking Balance..."):
                account_balance = chain_manager.get_balance(wallet.coldkeypub.to_checksum_address())
                opendata.__console__.print(
                    "Balance: [green]{}[/green]".format(account_balance)
                )

        # Get amount.
        if not config.get("amount"):
            amount = Prompt.ask("Enter DAT amount to transfer")
            if not config.no_prompt:
                try:
                    config.amount = float(amount)
                except ValueError:
                    console.print(
                        ":cross_mark:[red] Invalid DAT amount[/red] [bold white]{}[/bold white]".format(
                            amount
                        )
                    )
                    sys.exit()
            else:
                console.print(
                    ":cross_mark:[red] Invalid DAT amount[/red] [bold white]{}[/bold white]".format(
                        amount
                    )
                )
                sys.exit(1)

    @staticmethod
    def add_args(parser: argparse.ArgumentParser):
        transfer_parser = parser.add_parser(
            "transfer", help="""Transfer DAT between accounts."""
        )
        transfer_parser.add_argument("--dest", dest="dest", type=str, required=False)
        transfer_parser.add_argument(
            "--amount", dest="amount", type=float, required=False
        )

        opendata.Wallet.add_args(transfer_parser)
        opendata.ChainManager.add_args(transfer_parser)

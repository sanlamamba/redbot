#!/usr/bin/env python3
"""
Reset Bot Script - Make bot leave all servers

This script connects to Discord and makes the bot leave all servers it's currently in.
Useful for:
- Resetting bot to clean state
- Removing bot from test servers
- Starting fresh deployment

CAUTION: This will remove the bot from ALL servers. Use with care!
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

# Color codes for terminal
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class ResetBot(commands.Bot):
    """Bot that leaves all servers and then exits."""

    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.servers_left = 0
        self.total_servers = 0

    async def on_ready(self):
        """When bot is ready, leave all servers."""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}  Bot Reset Script{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")

        print(f"Logged in as: {GREEN}{self.user.name}{RESET} (ID: {self.user.id})")

        self.total_servers = len(self.guilds)

        if self.total_servers == 0:
            print(f"\n{YELLOW}ℹ{RESET}  Bot is not in any servers.")
            await self.close()
            return

        print(f"\n{YELLOW}⚠{RESET}  Found {RED}{self.total_servers}{RESET} server(s):")
        print(f"{BLUE}{'─'*70}{RESET}\n")

        for guild in self.guilds:
            print(f"  • {guild.name} (ID: {guild.id}) - {guild.member_count} members")

        print(f"\n{BLUE}{'─'*70}{RESET}")
        print(f"\n{RED}⚠ WARNING:{RESET} This will make the bot leave ALL servers!")

        # Ask for confirmation
        try:
            response = input(f"\n{YELLOW}Type 'yes' to confirm:{RESET} ").strip().lower()
        except EOFError:
            print(f"\n{RED}✗{RESET} Cancelled (no input)")
            await self.close()
            return

        if response != 'yes':
            print(f"\n{YELLOW}✗{RESET} Cancelled by user")
            await self.close()
            return

        print(f"\n{BLUE}{'─'*70}{RESET}")
        print(f"{YELLOW}Leaving servers...{RESET}\n")

        # Leave all servers
        for guild in self.guilds:
            try:
                await guild.leave()
                self.servers_left += 1
                print(f"  {GREEN}✓{RESET} Left: {guild.name}")
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"  {RED}✗{RESET} Failed to leave {guild.name}: {e}")

        print(f"\n{BLUE}{'─'*70}{RESET}")
        print(f"\n{GREEN}✓{RESET} Successfully left {GREEN}{self.servers_left}{RESET}/{self.total_servers} servers")

        if self.servers_left < self.total_servers:
            print(f"{YELLOW}⚠{RESET} Failed to leave {self.total_servers - self.servers_left} server(s)")

        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{GREEN}Reset complete!{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")

        await self.close()


async def show_servers_only():
    """Just show which servers the bot is in without leaving."""

    class ShowBot(commands.Bot):
        async def on_ready(self):
            print(f"\n{BLUE}{'='*70}{RESET}")
            print(f"{BLUE}  Bot Server Information{RESET}")
            print(f"{BLUE}{'='*70}{RESET}\n")

            print(f"Logged in as: {GREEN}{self.user.name}{RESET} (ID: {self.user.id})")
            print(f"Total servers: {GREEN}{len(self.guilds)}{RESET}\n")

            if len(self.guilds) == 0:
                print(f"{YELLOW}ℹ{RESET}  Bot is not in any servers.\n")
            else:
                print(f"{BLUE}{'─'*70}{RESET}\n")
                for i, guild in enumerate(self.guilds, 1):
                    owner = guild.owner
                    owner_name = f"{owner.name}" if owner else "Unknown"

                    print(f"{i}. {GREEN}{guild.name}{RESET}")
                    print(f"   ID: {guild.id}")
                    print(f"   Members: {guild.member_count}")
                    print(f"   Owner: {owner_name}")
                    print(f"   Created: {guild.created_at.strftime('%Y-%m-%d')}")

                    # Count channels
                    text_channels = len(guild.text_channels)
                    voice_channels = len(guild.voice_channels)
                    print(f"   Channels: {text_channels} text, {voice_channels} voice")
                    print()

                print(f"{BLUE}{'─'*70}{RESET}\n")

            print(f"{BLUE}{'='*70}{RESET}\n")
            await self.close()

    intents = discord.Intents.default()
    bot = ShowBot(command_prefix="!", intents=intents)

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print(f"{RED}✗{RESET} DISCORD_TOKEN not found in .env file")
        return

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user{RESET}")
    except Exception as e:
        print(f"{RED}✗{RESET} Error: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Reset bot by leaving all servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/reset_bot.py              # Leave all servers (with confirmation)
  python scripts/reset_bot.py --show       # Just show current servers
  python scripts/reset_bot.py --force      # Leave all servers without confirmation
        """
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Only show servers, don't leave them"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt (DANGEROUS!)"
    )

    args = parser.parse_args()

    # Check for Discord token
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print(f"\n{RED}✗{RESET} DISCORD_TOKEN not found in .env file")
        print(f"{YELLOW}→{RESET} Make sure .env file exists with DISCORD_TOKEN set\n")
        sys.exit(1)

    if args.show:
        # Just show servers
        asyncio.run(show_servers_only())
    else:
        # Leave all servers
        if args.force:
            # Monkey patch input to auto-confirm
            import builtins
            builtins.input = lambda _: "yes"

        intents = discord.Intents.default()
        bot = ResetBot()

        try:
            bot.run(token)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupted by user{RESET}")
        except Exception as e:
            print(f"\n{RED}✗{RESET} Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()

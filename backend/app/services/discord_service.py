"""Discord bot service for sending notifications."""

import discord
import asyncio
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class DiscordBot:
    """Discord bot for sending notifications to a configured channel."""

    def __init__(self):
        """Initialize the Discord bot (not connected yet)."""
        self.bot: Optional[discord.Client] = None
        self.channel_id: Optional[int] = None
        self.is_running = False
        self._bot_task: Optional[asyncio.Task] = None

    async def start(self, token: str, channel_id: int):
        """
        Start the Discord bot with the given token and channel ID.

        Args:
            token: Discord bot token
            channel_id: Channel ID to send notifications to
        """
        if self.is_running:
            logger.warning("Discord bot is already running")
            return

        self.channel_id = channel_id

        # Create bot with minimal intents (we only send messages, don't need events)
        intents = discord.Intents.default()
        intents.message_content = False  # We don't read messages
        intents.guilds = True  # Need this to see guilds and channels

        self.bot = discord.Client(intents=intents)

        @self.bot.event
        async def on_ready():
            logger.info(f"Discord bot logged in as {self.bot.user}")
            self.is_running = True

        @self.bot.event
        async def on_error(event, *args, **kwargs):
            logger.error(f"Discord bot error in {event}: {args}, {kwargs}")

        try:
            # Start bot in background task
            self._bot_task = asyncio.create_task(self.bot.start(token))

            # Wait for bot to be ready
            for _ in range(10):  # Wait up to 5 seconds
                await asyncio.sleep(0.5)
                if self.is_running:
                    break

            if not self.is_running:
                raise Exception("Discord bot failed to connect within 5 seconds")

        except discord.LoginFailure:
            logger.error("Invalid Discord bot token")
            raise ValueError("Invalid Discord bot token")
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            raise

    async def stop(self):
        """Stop the Discord bot."""
        if self.bot and not self.bot.is_closed():
            await self.bot.close()
            self.is_running = False

        if self._bot_task:
            self._bot_task.cancel()
            try:
                await self._bot_task
            except asyncio.CancelledError:
                pass

    async def send_message(self, content: str) -> bool:
        """
        Send a message to the configured channel.

        Args:
            content: Message content to send

        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.is_running or not self.bot:
            logger.error("Discord bot is not running")
            return False

        if not self.channel_id:
            logger.error("No channel ID configured")
            return False

        try:
            channel = await self.bot.fetch_channel(self.channel_id)
            if not channel:
                logger.error(f"Channel {self.channel_id} not found")
                return False

            await channel.send(content)
            logger.info(f"Sent Discord message to channel {self.channel_id}")
            return True

        except discord.Forbidden:
            logger.error(
                f"Bot doesn't have permission to send messages to channel {self.channel_id}"
            )
            return False
        except discord.HTTPException as e:
            logger.error(f"Failed to send Discord message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Discord message: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if bot is connected and ready."""
        return self.is_running and self.bot and not self.bot.is_closed()

    async def fetch_channels(self) -> List[dict]:
        """
        Fetch list of text channels the bot has access to.

        Returns:
            List of channel dicts with id, name, type, position
        """
        if not self.is_running or not self.bot:
            logger.error("Discord bot is not running")
            return []

        try:
            channels = []
            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    channels.append(
                        {
                            "id": str(channel.id),
                            "name": channel.name,
                            "guild_name": guild.name,
                            "position": channel.position,
                        }
                    )

            # Sort by guild name, then by position
            channels.sort(key=lambda c: (c["guild_name"], c["position"]))
            logger.info(
                f"Fetched {len(channels)} channels from {len(self.bot.guilds)} guilds"
            )
            return channels

        except Exception as e:
            logger.error(f"Failed to fetch Discord channels: {e}")
            return []


class NotificationFormatter:
    """Format notifications for Discord messages."""

    @staticmethod
    def format_action_notification(
        day_name: str, person_name: str, action: str, recipe_name: Optional[str] = None
    ) -> str:
        """
        Format a daily action notification.

        Example: "Today: Bob is cooking Tikka Masala"
        """
        action_verb_map = {
            "cook": "cooking",
            "shop": "shopping",
            "takeout": "ordering takeout",
            "rest": "taking a rest day",
            "leftovers": "eating leftovers",
        }

        action_verb = action_verb_map.get(action.lower(), action)

        if recipe_name and action.lower() == "cook":
            return f"**{day_name}:** {person_name} is {action_verb} **{recipe_name}**"
        else:
            return f"**{day_name}:** {person_name} is {action_verb}"

    @staticmethod
    def format_shopping_notification(shopping_date: str, items: List[dict]) -> str:
        """
        Format a shopping notification with grocery list.

        Args:
            shopping_date: Shopping date string
            items: List of grocery items with keys: ingredient_name, total_quantity, unit
        """
        lines = [
            f"**Shopping List for {shopping_date}**",
            "",
        ]

        for item in items:
            quantity = item.get("total_quantity", 0)
            unit = item.get("unit", "")
            name = item.get("ingredient_name", "")
            lines.append(f"• {quantity} {unit} {name}")

        lines.append("")
        lines.append(f"Total items: {len(items)}")

        return "\n".join(lines)

    @staticmethod
    def format_week_transition(
        theme_name: str, week_number: int, assignments_summary: List[dict]
    ) -> str:
        """
        Format a week transition notification.

        Args:
            theme_name: Week theme name
            week_number: Week number in sequence
            assignments_summary: List of dicts with keys: person_name, days (list of day names)

        Example: "New week starting: Burger Week. Bob cooks Mon & Wed, Alice Thu & Fri"
        """
        lines = [
            f"**New week starting: {theme_name}** (Week {week_number})",
            "",
        ]

        for assignment in assignments_summary:
            person = assignment.get("person_name", "Unknown")
            days = assignment.get("days", [])
            if days:
                days_str = " & ".join(days)
                lines.append(f"• {person}: {days_str}")

        return "\n".join(lines)

    @staticmethod
    def format_template_retirement(
        template_name: str, affected_sequences: List[dict]
    ) -> str:
        """
        Format a template retirement notification.

        Args:
            template_name: Name of the retired template
            affected_sequences: List of dicts with keys: sequence_name, old_position, new_position

        Example: "Burger Week has been retired and removed from 2 schedules."
        """
        if not affected_sequences:
            return f"🗑️ **{template_name}** has been retired."

        lines = [
            f"🗑️ **{template_name}** has been retired and removed from {len(affected_sequences)} schedule{'s' if len(affected_sequences) > 1 else ''}.",
            "",
        ]

        for seq in affected_sequences:
            sequence_name = seq.get("sequence_name", "Unknown Schedule")
            old_pos = seq.get("old_position", "?")
            new_pos = seq.get("new_position", "?")
            lines.append(
                f"• **{sequence_name}**: Auto-advanced from position {old_pos} to {new_pos}"
            )

        return "\n".join(lines)


# Global bot instance
_bot_instance: Optional[DiscordBot] = None


def get_bot() -> DiscordBot:
    """Get the global Discord bot instance."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = DiscordBot()
    return _bot_instance

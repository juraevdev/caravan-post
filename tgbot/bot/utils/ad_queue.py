import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from django.db import transaction
from asgiref.sync import sync_to_async

from tgbot.models import AdCounter, Advertisement

logger = logging.getLogger(__name__)


class AdQueue:
    """Queue system for flood prevention and batch posting"""
    
    def __init__(self):
        self.queues: Dict[str, List[Advertisement]] = {}  # channel_username -> list of ads
        self.timers: Dict[str, asyncio.Task] = {}  # channel_username -> timer task
        self.lock = asyncio.Lock()
    
    async def add_ad(self, channel_username: str, user_telegram_id: int, 
                    user_full_name: str, user_username: str, message_text: str, message_id: int = None) -> str:
        """
        Add advertisement to queue and generate ID
        
        Args:
            channel_username: Target channel username
            user_telegram_id: User's Telegram ID
            user_full_name: User's full name
            user_username: User's username (optional)
            message_text: Advertisement text
            message_id: Original message ID for forwarding
            
        Returns:
            str: Generated advertisement ID
        """
        async with self.lock:
            # Generate ad ID
            ad_id = await self._generate_ad_id(channel_username)
            
            # Create advertisement record
            ad = await sync_to_async(Advertisement.objects.create)(
                ad_id=ad_id,
                channel_username=channel_username,
                user_telegram_id=user_telegram_id,
                user_full_name=user_full_name,
                user_username=user_username,
                message_text=message_text,
                original_message_id=message_id,
                is_posted=False
            )
            
            # Add to queue
            if channel_username not in self.queues:
                self.queues[channel_username] = []
            
            self.queues[channel_username].append(ad)
            
            # Start timer if not already running
            if channel_username not in self.timers or self.timers[channel_username].done():
                self.timers[channel_username] = asyncio.create_task(
                    self._schedule_post(channel_username)
                )
            
            logger.info(f"Added ad {ad_id} to queue for @{channel_username}")
            return ad_id
    
    async def _generate_ad_id(self, channel_username: str) -> str:
        """
        Generate unique ad ID based on channel prefix
        
        Args:
            channel_username: Channel username to determine prefix
            
        Returns:
            str: Generated ad ID (e.g., TJ00000001, KZ00000001)
        """
        # Determine prefix based on channel
        prefix = self._get_channel_prefix(channel_username)
        
        # Get and increment counter
        @sync_to_async
        def get_next_id():
            with transaction.atomic():
                counter, created = AdCounter.objects.get_or_create(
                    channel_prefix=prefix,
                    defaults={'last_id': 0}
                )
                counter.last_id += 1
                counter.save()
                return counter.last_id
        
        next_id = await get_next_id()
        
        # Format ID with leading zeros
        return f"{prefix}{next_id:08d}"
    
    def _get_channel_prefix(self, channel_username: str) -> str:
        """Get prefix for channel based on username"""
        channel_mapping = {
            "Borkashoni_Tojikiston": "TJ",
            "JukGruz_Kazakstan": "KZ",
            "YukBirja_Turkmen": "TM",
            "JukGruz_KG": "KG",
            "YukMarkazi_Caravan": "CM",
        }
        return channel_mapping.get(channel_username, "XX")  # XX for unknown channels
    
    async def _schedule_post(self, channel_username: str):
        """
        Schedule batch posting after 60 seconds
        
        Args:
            channel_username: Channel to post ads to
        """
        try:
            # Wait 60 seconds
            await asyncio.sleep(60)
            
            # Post all ads in queue
            await self._post_batch(channel_username)
            
        except asyncio.CancelledError:
            logger.info(f"Timer cancelled for @{channel_username}")
        except Exception as e:
            logger.error(f"Error in timer for @{channel_username}: {e}")
    
    async def _post_batch(self, channel_username: str):
        """
        Forward all queued ads individually to preserve sender info
        
        Args:
            channel_username: Channel to post ads to
        """
        async with self.lock:
            if channel_username not in self.queues or not self.queues[channel_username]:
                return
            
            ads_to_post = self.queues[channel_username].copy()
            self.queues[channel_username].clear()
            
            if not ads_to_post:
                return
        
        try:
            from tgbot.bot.loader import bot
            posted_message_ids = []
            
            # Forward each ad individually to preserve sender information
            for ad in ads_to_post:
                try:
                    # Forward the original message from user to channel
                    if ad.original_message_id:
                        sent_message = await bot.forward_message(
                            chat_id=f"@{channel_username}",
                            from_chat_id=ad.user_telegram_id,
                            message_id=ad.original_message_id
                        )
                        
                        # Edit the forwarded message to add ID as prefix
                        if sent_message.text:
                            new_text = f"🆔 <b>{ad.ad_id}</b>\n\n{sent_message.text}"
                            await bot.edit_message_text(
                                chat_id=f"@{channel_username}",
                                message_id=sent_message.message_id,
                                text=new_text,
                                parse_mode="HTML"
                            )
                        elif sent_message.caption:
                            new_caption = f"🆔 <b>{ad.ad_id}</b>\n\n{sent_message.caption}"
                            await bot.edit_message_caption(
                                chat_id=f"@{channel_username}",
                                message_id=sent_message.message_id,
                                caption=new_caption,
                                parse_mode="HTML"
                            )
                        
                        posted_message_ids.append(sent_message.message_id)
                    else:
                        # If we don't have the original message_id, send as formatted text with ID
                        formatted_message = f"🆔 <b>{ad.ad_id}</b>\n\n{ad.message_text}"
                        sent_message = await bot.send_message(
                            chat_id=f"@{channel_username}",
                            text=formatted_message
                        )
                        posted_message_ids.append(sent_message.message_id)
                    
                except Exception as e:
                    logger.error(f"Error forwarding ad {ad.ad_id}: {e}")
                    # Try to send as formatted text if forwarding fails
                    try:
                        formatted_message = f"🆔 <b>{ad.ad_id}</b>\n\n{ad.message_text}"
                        sent_message = await bot.send_message(
                            chat_id=f"@{channel_username}",
                            text=formatted_message
                        )
                        posted_message_ids.append(sent_message.message_id)
                    except Exception as e2:
                        logger.error(f"Error sending formatted ad {ad.ad_id}: {e2}")
                        continue
            
            # Update ads with message_id and mark as posted
            if posted_message_ids:
                @sync_to_async
                def update_ads():
                    for i, ad in enumerate(ads_to_post):
                        if i < len(posted_message_ids):
                            Advertisement.objects.filter(ad_id=ad.ad_id).update(
                                message_id=posted_message_ids[i],
                                is_posted=True
                            )
                
                await update_ads()
            
            logger.info(f"Posted batch of {len(ads_to_post)} ads to @{channel_username}")
            
        except Exception as e:
            logger.error(f"Error posting batch to @{channel_username}: {e}")
            
            # Re-add ads to queue if posting failed
            async with self.lock:
                self.queues[channel_username].extend(ads_to_post)
    
    def _format_combined_message(self, ads: List[Advertisement]) -> str:
        """
        Format combined message with all ads
        
        Args:
            ads: List of advertisements to format
            
        Returns:
            str: Formatted combined message
        """
        if not ads:
            return ""
        
        message_parts = []
        
        for ad in ads:
            # Format each ad
            ad_text = f"<b>{ad.ad_id}</b>\n"
            ad_text += f"{ad.message_text}\n"
            # ad_text += "------------------"
            
            message_parts.append(ad_text)
        
        # Join all ads with newlines
        return "\n\n".join(message_parts)
    
    async def get_queue_status(self) -> Dict[str, int]:
        """
        Get current queue status for all channels
        
        Returns:
            Dict: Channel username -> number of ads in queue
        """
        async with self.lock:
            return {channel: len(ads) for channel, ads in self.queues.items()}


# Global queue instance
ad_queue = AdQueue()

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TwilioMedia:
    url: str  # Twilio media URL
    content_type: str
    local_path: Optional[str] = None  # Path where media is saved locally

@dataclass
class TwilioMessage:
    message_sid: str
    body: str
    sender: str  # Phone number without whatsapp: prefix
    recipient: str
    media: List[TwilioMedia]
    direction: str  # 'inbound' or 'outbound'
    timestamp: str
    status: str = 'received'
    
    @property
    def has_media(self) -> bool:
        return len(self.media) > 0

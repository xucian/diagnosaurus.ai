"""
GeoIP service for location lookup
Uses local database for simplicity (no external API calls)
"""
import json
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger
from config import settings


class GeoIPService:
    """Local GeoIP lookup service"""

    def __init__(self):
        """Initialize with local GeoIP database"""
        self.db_path = settings.geoip_db_path
        self.db = self._load_database()
        logger.info("GeoIP service initialized")

    def _load_database(self) -> Dict[str, Any]:
        """Load GeoIP database from JSON file"""
        try:
            if not self.db_path.exists():
                logger.warning(f"GeoIP database not found at {self.db_path}, using fallback")
                return self._get_fallback_database()

            with open(self.db_path, "r") as f:
                db = json.load(f)
                logger.info(f"Loaded GeoIP database with {len(db)} entries")
                return db

        except Exception as e:
            logger.error(f"Failed to load GeoIP database: {e}")
            return self._get_fallback_database()

    def _get_fallback_database(self) -> Dict[str, Any]:
        """Fallback database for common IP ranges"""
        return {
            "default": {
                "city": "San Francisco",
                "country": "United States",
                "latitude": 37.7749,
                "longitude": -122.4194,
            }
        }

    def get_location(self, ip_address: str) -> Dict[str, Any]:
        """
        Get geographic location from IP address

        Args:
            ip_address: IPv4 or IPv6 address

        Returns:
            Dictionary with city, country, lat, lon
        """
        try:
            # Try exact match first
            if ip_address in self.db:
                return self.db[ip_address]

            # Try IP range matching (simplified)
            ip_prefix = ".".join(ip_address.split(".")[:3])
            for db_ip, location in self.db.items():
                if db_ip.startswith(ip_prefix):
                    logger.debug(f"Found location for IP {ip_address}: {location['city']}")
                    return location

            # Fallback to default location
            logger.warning(f"No location found for IP {ip_address}, using default")
            return self.db.get("default", {
                "city": "Unknown",
                "country": "Unknown",
                "latitude": 0.0,
                "longitude": 0.0,
            })

        except Exception as e:
            logger.error(f"GeoIP lookup failed: {e}")
            return self.db.get("default")

    def get_location_from_request(self, request) -> Dict[str, Any]:
        """
        Extract location from Flask request object

        Args:
            request: Flask request object

        Returns:
            Location dictionary
        """
        # Try to get IP from headers (handles proxies)
        ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.headers.get("X-Real-IP", "") or
            request.remote_addr or
            "127.0.0.1"
        )

        # Special handling for local development
        if ip in ["127.0.0.1", "localhost", "::1"]:
            logger.debug("Local IP detected, using default location")
            return self.db.get("default")

        return self.get_location(ip)


# Global instance
geoip_service = GeoIPService()

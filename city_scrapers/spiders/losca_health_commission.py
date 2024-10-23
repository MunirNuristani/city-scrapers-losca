from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider

from dateutil.parser import parse


class LoscaHealthCommissionSpider(CityScrapersSpider):
    name = "losca_health_commission"
    agency = "Los Angeles Health Commission"
    timezone = "America/Los_Angeles"
    committee_id: int = 6
    start_year: int = 2024
    default_location = {
        "address": "200 N Spring St, Room 340 (CITY HALL) Los Angeles, CA 90012",
        "name": "Los Angeles City Health Commission",
    }
    start_urls = [f"https://lacity.primegov.com/api/v2/PublicPortal/ListArchivedMeetingsByCommitteeId?year={start_year}&committeeId={committee_id}"]

    def parse(self, response):
        """
        This spider retrieves meetings for the specified `start_year`.
        Update `start_year` to change the target year.
        """
        try:
            items = response.json()
            if not isinstance(items, list):
                self.logger.error(f"Expected list of items, got {type(items)}")
                return

            for item in items:
                required_fields = ['title', 'dateTime', 'videoUrl', 'documentList']
                if not all(field in item for field in required_fields):
                    self.logger.warning(f"Missing required fields in item: {item}")
                    continue
                
                meeting = Meeting(
                    title=self._parse_title(item),
                    description=self._parse_description(item),
                    classification=self._parse_classification(item),
                    start=self._parse_start(item),
                    end=self._parse_end(item),
                    all_day=self._parse_all_day(item),
                    time_notes=self._parse_time_notes(item),
                    location=self._parse_location(item),
                    links=self._parse_links(item),
                    source=self._parse_source(response),
                )

                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)

                yield meeting
        except ValueError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        return item["title"] if item["title"] else ""

    def _parse_description(self, item):
        """Parse or generate meeting description."""
        return ""

    def _parse_classification(self, item):
        """Parse or generate classification from allowed options."""
        return COMMISSION

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        try:
            return parse(item["dateTime"])
        except (ValueError, TypeError) as e:
            self.logger.error(f"Failed to parse datetime '{item.get('dateTime')}': {e}")
            return None

    def _parse_end(self, item):
        """Parse end datetime as a naive datetime object. Added by pipeline if None"""
        return None

    def _parse_time_notes(self, item):
        """Parse any additional notes on the timing of the meeting"""
        return ""

    def _parse_all_day(self, item):
        """Parse or generate all-day status. Defaults to False."""
        return False

    def _parse_location(self, item):
        """Parse or generate location."""
        return self.default_location.copy()

    def _parse_links(self, item):
        """Parse or generate links.
        
        Link types:
        - videoUrl: Direct link to meeting video
        - compileOutputType 3: Meeting template link
        - compileOutputType 1: Compiled document link
        """
        COMPILE_OUTPUT_TYPES = {
            3: "https://lacity.primegov.com/Portal/Meeting?meetingTemplateId={}",
            1: "https://lacity.primegov.com/Public/CompiledDocument?meetingTemplateId={}&compileOutputType=1"
        }
        data = []
        data.append({
            "href": item["videoUrl"],
            "title": "videoLink"
        })
        for document in item["documentList"]:
            output_type = document["compileOutputType"]
            if output_type in COMPILE_OUTPUT_TYPES:
                data.append({
                    "href": COMPILE_OUTPUT_TYPES[output_type].format(document["templateId"]),
                    "title": document["templateName"]
                })
        return data

    def _parse_source(self, response):
        """Parse or generate source."""
        return response.url

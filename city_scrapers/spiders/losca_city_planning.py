import json
import re
from dateutil.parser import parse
from city_scrapers_core.constants import NOT_CLASSIFIED, COMMISSION, BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class LoscaCityPlanningSpider(CityScrapersSpider):
    name = "losca_city_planning"
    agency = "Los Angeles City Planning"
    timezone = "America/Chicago"
    start_urls =[ "https://planning.lacity.gov/dcpapi/meetings/api/all/commissions/2024", 
                  "https://planning.lacity.gov/dcpapi/meetings/api/all/boards/2024", 
                  "https://planning.lacity.gov/dcpapi/meetings/api/all/hearings/2024"
                ]


    def parse(self, response):

        """
        This spider will get the meetings for the year 2024. 
        for previous years, `start_urls` needs to be changed. 
        """
        data = json.loads(response.body)
        items = data["Entries"]

        for item in items:
            meeting = Meeting(
                title=item["Type"],
                description=item["Note"],
                classification=self._parse_classification(item),
                start=parse(item["Date"]),
                end= None,
                all_day= False,
                time_notes= "",
                location=self._parse_location(item),
                links=self._parse_links(item),
                source=self._parse_source(response),
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting



    def _parse_location(self, item):
        """Parse or generate location."""
        pattern = r'(\d{3,4}(?:\s?–\s?\d{3,4})?(?:\s?and\s?\d{3,4})?(?:\s?,?\s?\d{3,4})?\s[\w\s]+\b(?:Road|Drive|Boulevard|Avenue))'
        addresses = re.findall(pattern, item["Address"])

        return {
            "address": addresses,
            "name": item["BoardName"],
        }

    def _parse_links(self, item):
        """Parse or generate links."""
        links = []

        if "AgendaLink" in item and item["AgendaLink"]:
            links.append({
                "href": item["AgendaLink"],
                "title": item["Agenda"]
            })
            
        if "AddDocsLink" in item and item["AddDocsLink"]:
            links.append({
                "href": item["AddDocsLink"],
                "title": item["AddDocs"]
            })

        return links if links else None

    def _parse_classification(self, item):
        lower_text = item["Type"].lower()
        switch_case = {
        "board": BOARD,
        "commission": COMMISSION,
        }
        for key, value in switch_case.items():
            if key in lower_text:
                return value
        return NOT_CLASSIFIED    


    def _parse_source(self, response):
        """Parse or generate source."""
        return response.url
    

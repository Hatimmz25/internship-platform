BOT_NAME = "internship_scraper"

SPIDER_MODULES = ["internship_scraper.spiders"]
NEWSPIDER_MODULE = "internship_scraper.spiders"

ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 4
DOWNLOAD_DELAY = 1.0

ITEM_PIPELINES = {
   "internship_scraper.pipelines.ContentDeduplicationPipeline": 100,
   "internship_scraper.pipelines.KeywordFilterPipeline": 200,
}
# Standard library imports

# 3rd party library imports

# local imports
from .common import CommonHarvester


class D1TestToolAsync(CommonHarvester):

    def __init__(self, sitemap_url=None, **kwargs):
        super().__init__(id='d1checksite', **kwargs)

        self.site_map = sitemap_url
        self.logger.debug(f'num_workers = {self.num_workers}')

    @classmethod
    async def create(cls, **kwargs):
        self = D1TestToolAsync(**kwargs)
        await self._async_finish_init()
        await self.run()
        await self._async_close()

    async def harvest_document(self, doi, doc, record_date):
        """
        We don't actually harvest.
        """
        pass

    def summarize(self):
        """
        We don't harvest, so summarization is much simpler.
        """
        msg = f'Successfully processed {self.created_count} records.'
        self.logger.info(msg)


async def run_test_tool(d1_test_tool):
    """
    See https://stackoverflow.com
        /questions/33128325
        /how-to-set-class-attribute-with-await-in-init/33134213
    for the reason behind this.  asyncio not well adapted to magic methods just
    yet, it would seem.
    """
    await d1_test_tool._async_finish_init()
    await d1_test_tool.run()
    await d1_test_tool._async_close()
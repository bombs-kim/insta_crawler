class MyCustomDownloaderMiddleware(object):

    def process_request(self, request, spider):
        #logging.debug('MIDDLEWARE CALLED')
        request.meta['proxy'] = 'http://proxypool.daumsoft.com:7012'

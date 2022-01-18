import scrapy
from urllib import parse
from collections import OrderedDict


# 工具方法，截断字符串，参考StringUtils.substringBetween
def substring_between(str, open, close):
    start = str.index(open);
    if start != -1:
        end = str.index(close, start + len(open))
        if end != -1:
            return str[start + len(open):end]
    return None


def gbk2utf8(str):
    decode = str.encode('gbk')
    result = parse.quote(decode)
    return result


class MyShopSpider(scrapy.Spider):
    name = 'MyShopSpider'
    allowed_domains = ['manmanbuy.com']
    # http://s.manmanbuy.com/Default.aspx?key=%D0%A1%C3%D712+Pro
    # http://s.manmanbuy.com/Default.aspx?key=小米12 Pro
    search = "小米12 Pro"
    start_url = 'http://s.manmanbuy.com/Default.aspx?key='

    def start_requests(self):
        search = gbk2utf8(self.search)
        url = self.start_url + search
        print(url)
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        title = response.xpath('/html/head/title/text()')
        print(title)

        print("+++>>" + response.url)
        select = scrapy.Selector(response)
        divs = select.xpath('//*[@id="listpro"]/div/div[@class="div1100"]/div')
        for one_div in divs:
            goods_title = ''.join(one_div.xpath('./div[@class="title"]/div[@class="t"]//*/text()').extract()).strip()
            if not goods_title: continue  # 如果标题为空,说明不是一个有效的div,跳过该div获取数据流程
            data_dict = OrderedDict()
            data_dict['商品标题'] = goods_title
            # 这有一个问题就是 个别url是: '/productdetail.aspx?itemid=558550356564&skuid='
            # /jdDetail.aspx?originalUrl=https://item.jd.com/100031406046.html&skuid=&proid=0
            # 通过慢慢买官网我们可以知道实质链接是:'https://detail.tmall.com/item.htm?id=558550356564&sku_properties=10004:709990523;5919063:6536025;12304035:3222911'
            # 有效的部分是 'https://detail.tmall.com/item.htm?id=558550356564',所以这里要做一个转换
            goods_href = str(one_div.xpath('./div[@class="title"]/div[@class="t"]/a/@href').get().strip())
            if goods_href.startswith('/productdetail.aspx?'):
                data_dict['商品链接'] = 'https://detail.tmall.com/item.htm?id=' + substring_between(goods_href, 'itemid=', '&')
            elif goods_href.startswith('/jdDetail.aspx?'):
                data_dict['商品链接'] = substring_between(goods_href, 'originalUrl=', '&')
            else:
                data_dict['商品链接'] = goods_href
            data_dict['商品价格'] = ''.join(
                one_div.xpath('./div[@class="cost"]/div[@class="p AreaPrice"]//*/text()').extract()).strip()
            data_dict['商城店铺'] = ''.join(one_div.xpath('./div[@class="mall"]').xpath(
                'p[@class="m"]//*/text()|./p[@class="AreaZY"]/text()').extract()).strip()
            data_dict['最新时间'] = one_div.xpath('./div[@class="mall"]/p[@class="t"]/text()').get().strip()
            # 这里作数据持久化操作,这里作打印操作
            print(data_dict['商品标题'], '\n', data_dict['商品链接'], '\n', data_dict['商品价格'], '\n',
                  data_dict['商城店铺'], '\n', data_dict['最新时间'], end='\n\n')
            # self.pipeline_utils.data_dict(self.name, "慢慢买商品对比价", data_dict, print_len_list=[10, 10, 10, 10, 10, 10])

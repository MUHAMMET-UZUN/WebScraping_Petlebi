# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter



class PetlebiscraperclearPipeline:
    def process_item(self, item, spider):

        adapter = ItemAdapter(item)

        #string attributes strip
        field_names = adapter.field_names()
        for field_name in field_names:
            if field_name != 'product_description':
                try:
                    value = adapter.get(field_name)
                    value = str(value)
                    adapter[field_name] = value.strip()
                except Exception as e:
                    print(f"\n*****Strip error (passed) : {e}*****\n")

        #category names to lowercase
        lowercase_keys = ['product_category']
        for lowercase_key in lowercase_keys:
            value = adapter.get(lowercase_key)
            adapter[lowercase_key] = value.lower()

        #prices str to float
        price_keys = ['product_old_price','product_new_price']
        for price_key in price_keys:
            value = adapter.get(price_key)
            value = value.replace(' TL','')
            value = value.replace(',', '.')
            adapter[price_key] = float(value)

        #barcode str to int
        try:
            value = adapter.get('product_barcode')
            adapter['product_barcode'] = int(value) if value is not None else None
        except Exception as e:
            print(f"\n*****barcode parse error: {e}*****\n")
            adapter['product_barcode'] = None

            #productID str to int
        try:
            value = adapter.get('productID')
            adapter['productID'] = int(value)
        except Exception as e:
            print(f"\n*****productID parse error: {e}*****\n")
            adapter['productID'] = None

        product_image = adapter.get('product_image')
        value = product_image.replace('//','')
        adapter['product_image'] = str(value)

        return item


import mysql.connector
class SaveToMySQLPipeline:

    def __init__(self):
        self.conn = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            password = '1234',
            database = 'petlebi'
        )

        self.cur = self.conn.cursor()

        self.cur.execute("""
                        CREATE TABLE IF NOT EXISTS petlebi_data(
                         id int NOT NULL auto_increment,
                         productID int,
                         url VARCHAR(255),
                         name VARCHAR(255),
                         barcode long,
                         image VARCHAR(255),
                         description text,
                         category VARCHAR (50),
                         brand VARCHAR(50),
                         new_price DECIMAL,
                         old_price DECIMAL,
                         stock VARCHAR(50),
                         sku VARCHAR(50),
                         PRIMARY KEY (id)
                        )""")
     
    def process_item(self, item, spider):
        self.cur.execute("""
                        insert into petlebi_data (
                         productID,
                         url,
                         name,
                         barcode,
                         image,
                         description,
                         category,
                         brand,
                         new_price,
                         old_price,
                         stock,
                         sku
                        ) values (
                         %s,
                         %s,
                         %s,
                         %s,
                         %s,
                         %s,
                         %s,
                         %s,
                         %s,
                         %s,
                         %s,
                         %s
                        )""",(
                        item["productID"],
                        item["product_url"],
                        item["product_name"],
                        item["product_barcode"],
                        item["product_image"],
                        item["product_description"],
                        item["product_category"],
                        item["product_brand"],
                        item["product_new_price"],
                        item["product_old_price"],
                        item["product_stock"],
                        item["sku"]
                    ))
        self.conn.commit()
        return item
    
    def close_spider(self,spider):

        self.cur.close()
        self.conn.close()
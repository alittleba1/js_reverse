from base import Base
import json


class CleanBuyinContactInfo(Base):
    name = 'buyin_contact_info'

    def __init__(self):
        super(CleanBuyinContactInfo, self).__init__()
        self.table = self.name
        self.clean_table = "clean_" + self.table

    def process_item(self, resp):
        list_res = []
        if not resp:
            self.log(f'清洗{self.table}数据-不存在')
            return ''

        for task_id, data, deduplication, update_time in resp:
            contact_info = json.loads(data).get('contact_info')
            item = {
                "task_id": task_id,
                "uid": deduplication.replace("uid=", ""),
                "times_left": contact_info.get('times_left'),
                "contact_value": contact_info.get('contact_value'),
                "deduplication": deduplication + '&contact_value=' + str(contact_info.get('contact_value')),
                "spider_time": update_time
            }
            list_res.append(item)
        db_res = self.eb_supports.insert_many(self.clean_table,
                                              list_res,
                                              conflict=[
                                                  "task_id", "uid", "times_left",
                                                  "contact_value", "contact_value", "deduplication",
                                                  "spider_time"
                                              ]
                                              )
        if db_res >= 0:
            return True, self.table, db_res
        else:
            return False, self.table, db_res


if __name__ == '__main__':
    offset = 0
    qc = CleanBuyinContactInfo()
    while True:
        sql = f"""
            select task_id, data, deduplication, update_time from buyin_contact_info where
             date_sub(CURDATE(),INTERVAL 2 DAY) <= DATE(update_time) LIMIT 1000 OFFSET {offset};
        """
        res = qc.eb_supports.query(sql)
        if not res:
            break
        qc.process_item(res)
        offset += 1000

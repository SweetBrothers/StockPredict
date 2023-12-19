import websocket
import json
import requests
import os
import asyncio
import time
import pymongo
# 암호화/복호화

from base64 import b64decode
from customToken import ApprovalCreater
clearConsole = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')


ouput_path = "./output"

class StockDataGetter:
    def __init__(self,code_list):
        self.setApproval()
        self.code_list = code_list
        # URL = 'ws://ops.koreainvestment.com:21000' # 실전계좌
        self.URL = 'ws://ops.koreainvestment.com:31000' # 모의계좌
        self.setApproval()
        self.mongo_url = 'mongodb://127.0.0.1:27017'
    
    def getCodeList(self):
        return code_list
    
    def setCodeList(self , code_list):
        self.code_list = code_list
    
    async def sendData(self):
        send_data_list = []
        for i,j,k in code_list:
            temp = '{"header":{"approval_key": "%s","custtype":"P","tr_type":"%s","content-type":"utf-8"},"body":{"input":{"tr_id":"%s","tr_key":"%s"}}}'%(self.approval_key,i,j,k)
            send_data_list.append(temp)
        ws = websocket.WebSocket()
        ws.connect(self.URL, ping_interval=60)
        for senddata in send_data_list:
            ws.send(senddata)
        while True:
            data = ws.recv()
            time.sleep(0.1)
            if data[0] == '0' or data[0] == '1':  # 실시간 데이터일 경우
                if data[0] == '0':
                    recvstr = data.split('|')  # 수신데이터가 실데이터 이전은 '|'로 나뉘어져있어 split
                    trid0 = recvstr[1]
                    if trid0 == "H0STASP0":  # 주식호가tr 일경우의 처리 단계
                        print("#### 주식호가 ####")
                        self.stockhoka(recvstr[3])
                        await asyncio.sleep(0.2)

                    # elif trid0 == "H0STCNT0":  # 주식체결 데이터 처리
                    #     print("#### 주식체결 ####")
                    #     data_cnt = int(recvstr[2])  # 체결데이터 개수
                    #     stockspurchase(data_cnt, recvstr[3])

                # elif data[0] == '1':
                #     print(data)
                #     recvstr = data.split('|')  # 수신데이터가 실데이터 이전은 '|'로 나뉘어져있어 split
                #     trid0 = recvstr[1]
                #     if trid0 == "H0STCNI0" or trid0 == "H0STCNI9":  # 주실체결 통보 처리
                #         print("#### 주식체결통보 ####")
                #         stocksigningnotice(recvstr[3], aes_key, aes_iv

            else:
                jsonObject = json.loads(data)
                trid = jsonObject["header"]["tr_id"]

                if trid != "PINGPONG":
                    rt_cd = jsonObject["body"]["rt_cd"]
                    if rt_cd == '1':    # 에러일 경우 처리
                        print("### ERROR RETURN CODE [ %s ] MSG [ %s ]" % (rt_cd, jsonObject["body"]["msg1"]))
                        pass
                    elif rt_cd == '0':  # 정상일 경우 처리
                        print("### RETURN CODE [ %s ] MSG [ %s ]" % (rt_cd, jsonObject["body"]["msg1"]))
                        # 체결통보 처리를 위한 AES256 KEY, IV 처리 단계
                        if trid == "H0STCNI0" or trid == "H0STCNI9":
                            aes_key = jsonObject["body"]["output"]["key"]
                            aes_iv = jsonObject["body"]["output"]["iv"]
                            print("### TRID [%s] KEY[%s] IV[%s]" % (trid, aes_key, aes_iv))

                # 웹소켓 연결이 끈기지 않기 위해 실행 
                elif trid == "PINGPONG":
                    print("### RECV [PINGPONG] [%s]" % (data))
                    print("### SEND [PINGPONG] [%s]" % (data))
        
        
    def setApproval(self):
        ac = ApprovalCreater()
        ac.createApproval()
        self.approval_key = ac.loadApproval()
        
    def stockhoka(self,data):
        recvvalue = data.split('^')  # 수신데이터를 split '^'
        
        
        
        hoka_json = {}
        hoka_json["code"] = recvvalue[0]
        hoka_json["time"] =  recvvalue[1]
        hoka_json["time_code"] =  recvvalue[2]
        hoka_json["selling"] = {}
        hoka_json["buying"] = {}
        for i in range(3,13):
            hoka_json["selling"][f"price{i-2}"] = recvvalue[i]
            hoka_json["selling"][f"remain{i-2}"] = recvvalue[i+20]
            hoka_json["buying"][f"price{i-2}"] = recvvalue[i+10]
            hoka_json["buying"][f"remain{i-2}"] = recvvalue[i+30]
        hoka_json["selling"]["remain_total"] = recvvalue[43]
        hoka_json["selling"]["remain_total_increase"] = recvvalue[54]
        hoka_json["buying"]["remain_total"] = recvvalue[44]
        hoka_json["buying"]["remain_total_increase"] = recvvalue[55]
        hoka_json["buying"]["outtime_remain_total"] = recvvalue[45]
        hoka_json["buying"]["outtime_remain_total_increase"] = recvvalue[46]
        hoka_json["selling"]["outtime_remain_total"] = recvvalue[56]
        hoka_json["selling"]["outtime_remain_total_increase"] = recvvalue[57]
        filename = hoka_json["code"] + recvvalue[1] +".json"
        
        
        filename = hoka_json["code"] + recvvalue[1] + ".txt"
        with open("./output/raw/"+filename, 'w', encoding='utf-8') as f:
            f.write(data)
        
        with pymongo.MongoClient(self.mongo_url) as conn:
            db_stock_data = conn["stock_data"]
            real_time_hocka_conn = db_stock_data["real_time_hocka"]
            real_time_hocka_conn.insert_one(hoka_json)
                    
            
        print("유가증권 단축 종목코드 [" + recvvalue[0] + "]")
        print("영업시간 [" + recvvalue[1] + "]" + "시간구분코드 [" + recvvalue[2] + "]")
        print("======================================")
        print("매도호가10 [%s]    잔량10 [%s]" % (recvvalue[12], recvvalue[32]))
        print("매도호가09 [%s]    잔량09 [%s]" % (recvvalue[11], recvvalue[31]))
        print("매도호가08 [%s]    잔량08 [%s]" % (recvvalue[10], recvvalue[30]))
        print("매도호가07 [%s]    잔량07 [%s]" % (recvvalue[9], recvvalue[29]))
        print("매도호가06 [%s]    잔량06 [%s]" % (recvvalue[8], recvvalue[28]))
        print("매도호가05 [%s]    잔량05 [%s]" % (recvvalue[7], recvvalue[27]))
        print("매도호가04 [%s]    잔량04 [%s]" % (recvvalue[6], recvvalue[26]))
        print("매도호가03 [%s]    잔량03 [%s]" % (recvvalue[5], recvvalue[25]))
        print("매도호가02 [%s]    잔량02 [%s]" % (recvvalue[4], recvvalue[24]))
        print("매도호가01 [%s]    잔량01 [%s]" % (recvvalue[3], recvvalue[23]))
        print("--------------------------------------")
        print("매수호가01 [%s]    잔량01 [%s]" % (recvvalue[13], recvvalue[33]))
        print("매수호가02 [%s]    잔량02 [%s]" % (recvvalue[14], recvvalue[34]))
        print("매수호가03 [%s]    잔량03 [%s]" % (recvvalue[15], recvvalue[35]))
        print("매수호가04 [%s]    잔량04 [%s]" % (recvvalue[16], recvvalue[36]))
        print("매수호가05 [%s]    잔량05 [%s]" % (recvvalue[17], recvvalue[37]))
        print("매수호가06 [%s]    잔량06 [%s]" % (recvvalue[18], recvvalue[38]))
        print("매수호가07 [%s]    잔량07 [%s]" % (recvvalue[19], recvvalue[39]))
        print("매수호가08 [%s]    잔량08 [%s]" % (recvvalue[20], recvvalue[40]))
        print("매수호가09 [%s]    잔량09 [%s]" % (recvvalue[21], recvvalue[41]))
        print("매수호가10 [%s]    잔량10 [%s]" % (recvvalue[22], recvvalue[42]))
        print("======================================")
        print("총매도호가 잔량        [%s]" % (recvvalue[43]))
        print("총매도호가 잔량 증감   [%s]" % (recvvalue[54]))
        print("총매수호가 잔량        [%s]" % (recvvalue[44]))
        print("총매수호가 잔량 증감   [%s]" % (recvvalue[55]))
        print("시간외 총매도호가 잔량 [%s]" % (recvvalue[45]))
        print("시간외 총매수호가 증감 [%s]" % (recvvalue[46]))
        print("시간외 총매도호가 잔량 [%s]" % (recvvalue[56]))
        print("시간외 총매수호가 증감 [%s]" % (recvvalue[57]))
        print("예상 체결가            [%s]" % (recvvalue[47]))
        print("예상 체결량            [%s]" % (recvvalue[48]))
        print("예상 거래량            [%s]" % (recvvalue[49]))
        print("예상체결 대비          [%s]" % (recvvalue[50]))
        print("부호                   [%s]" % (recvvalue[51]))
        print("예상체결 전일대비율    [%s]" % (recvvalue[52]))
        print("누적거래량             [%s]" % (recvvalue[53]))
        print("주식매매 구분코드      [%s]" % (recvvalue[58]))
        
        
if __name__ == "__main__":
    code_list = [
        ['1','H0STASP0','066570'],
        ['1','H0STASP0','000660'],
        ['1','H0STASP0','005930'],
        ]
    sdg = StockDataGetter(code_list)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sdg.sendData())
    loop.close()
    


# tr_type(거래타입) : "1" 등록, "2" 해제
# tr_id(거래ID) : 
#     "H0STCNT0" 실시간 주식 체결가, 
#     "H0STASP0" : 실시간 주식 호가, 
#     "H0STCNI0" : (실전) 실시간 주식 체결통보, 
#     "H0STCNI9" : (모의) 실시간 주식 체결통보

# tr_key(거래ID) : 
#     "종목코드" 입력(tr_id가 H0STCNT0 or H0STASP0일 경우), 
#     "HTS ID" 입력(tr_id가 H0STCNI0 or H0STCNI9일 경우)
import yaml
import requests
import json
import os
from datetime import datetime



    
    

class ApprovalCreater:
    def __init__(self):
        self.config_root = os.getcwd() + '/token/'
         # 토큰 로컬저장시 파일명 년월일
        self.file_name = 'KIS' + datetime.today().strftime("%Y%m%d") +".yaml"
        self.approval_tmp =  self.config_root + self.file_name
        self._cfg=self.loadCfg()

        
    def loadCfg(self):
        try:
            with open(self.config_root + 'kis_devlp.yaml', encoding='UTF-8') as f:
                return yaml.load(f, Loader=yaml.FullLoader)
        except Exception as e:
            print(f"Error: {e}")
            return False
            
    def getApproval(self,key, secret):
        """웹소켓 접속키 발급"""
        url = 'https://openapi.koreainvestment.com:9443'
        headers = {"content-type": "application/json"}
        body = {"grant_type": "client_credentials",
                "appkey": self._cfg[key],
                "secretkey": self._cfg[secret]}
        PATH = "oauth2/Approval"
        URL = f"{url}/{PATH}"
        res = requests.post(URL, headers=headers, data=json.dumps(body))
        approval_key = res.json()["approval_key"]
        return approval_key
    
    
    def saveApproval(self,my_approval):
        print('Save Approval date: ', self.file_name )
        with open(self.approval_tmp, 'w', encoding='utf-8') as f:
            f.write(f'token: {my_approval}\n')

        
    def loadApproval(self):
        try:
            # 토큰이 저장된 파일 읽기
            with open(self.approval_tmp, encoding='UTF-8') as f:
                tkg_tmp = yaml.load(f, Loader=yaml.FullLoader)
                return tkg_tmp['token']
        except Exception as e:
            print('read token error: ', e)
            return None
    
    def createApproval(self):
        # 접근토큰 관리하는 파일 존재여부 체크, 없으면 생성
        if os.path.exists(self.approval_tmp) == False:
            approval_key = self.getApproval("paper_app", "paper_sec")
            self.saveApproval(approval_key)

        else: 
            print("Aleady have web Socket Key")
     
     
     
     
class TokenCreater(ApprovalCreater):
    def __int__(self):
        super().__init__()
        self.file_name = "TOKEN_"+self.file_name    

#test
# if __name__ == "__main__":
#     ac = ApprovalCreater()
#     ac.createApproval()
#     a=ac.loadApproval()
#     print("key: ",a)

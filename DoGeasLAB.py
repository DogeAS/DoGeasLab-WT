#This is DoGeasLAB Controller

import asyncio
import logging
import pydglab
from pydglab import model_v3
import requests
import DGConfig as cfg

#参数区

#变量区
currentStA=0
currentStB=0
calculatedStA=0
calculatedStB=0
dglab_instance=pydglab.dglab_v3()
data={}
dataGot=False

#连接主机
async def connect():
    retry_count = 0
    await pydglab.scan()
    while retry_count < cfg.max_retries:
        try:
            print("正在连接...")
            await dglab_instance.create()
            print("成功连接！")
            return True  # 连接成功
        except Exception as e:
            retry_count += 1
            print(f"连接失败（尝试 {retry_count}/{cfg.max_retries}）：{e}")
            if retry_count < cfg.max_retries:
                print(f"{cfg.retry_delay} 秒后重试...")
                await asyncio.sleep(cfg.retry_delay)
            else:
                logging.error("已达到最大重试次数，连接失败。")
                return False  # 连接失败
            
#抓取数据
async def getData():
    global data,dataGot
    indicators_url = "http://localhost:8111/indicators"
    dataGot=True
    #获取数据
    try:
        response=requests.get(indicators_url)
        response.raise_for_status()
        data=response.json()
    #获取失败
    except requests.exceptions.RequestException as e:
        print(f"获取数据失败 :{e}")
        dataGot=False
        return 
    except ValueError as e:
        print(f"获取数据失败 : {e}")
        dataGot=False
        return 
    
#强度计算
async def setStrength():
    #计算
    global data,currentStA,currentStB,calculatedStA,calculatedStB
    calculatedStA=data.get("crew_total")*4
    calculatedStA=round(calculatedStA)
    #if calculatedStA<15:
        #calculatedStA+=5
    
#主逻辑
async def main():
    print("启动,准备连接")
    if not await connect():
        return  # 连接失败，退出函数
    #设置波形
    await dglab_instance.set_wave_sync(0, 0, 0, 0, 0, 0)
    await dglab_instance.set_wave_set(
        model_v3.Wave_set["Going_Faster"], model_v3.ChannelA
    )
    #连接成功，通电提醒
    await dglab_instance.set_strength_sync(cfg.wakeSignalStrength, cfg.wakeSignalStrength)
    await asyncio.sleep(1)
    await dglab_instance.set_strength_sync(cfg.defalutStrength,cfg.defalutStrength)
    #循环逻辑
    while True:
        await getData()
        await setStrength()
        #应用强度
        currentStA,currentStB=await dglab_instance.get_strength()
        if(calculatedStA!=currentStA or calculatedStB!=currentStB):
            print(f"强度修改为：{calculatedStA},{calculatedStB}")
            await dglab_instance.set_strength_sync(calculatedStA, calculatedStB)
        await asyncio.sleep(cfg.interval)
    return

if __name__ == "__main__":
    asyncio.run(main())
'''
  @Description      
  @auther         leizi
  @create          2020-03-14 09:40
'''
from config.config import Test_mobile_type, Test_plan_num, TestappPackage, TestAppActivity
from untils.StfTestPhoneUntil import StfPhoneOpear
import os, unittest,datetime,random
from multiprocessing import Pool
from testcase.regcasetest import regtest
from untils.Parmeris import Parmer
from untils.log import LOG
from  untils.makecase import makecasefile
from untils.pyreport_excel import create
from untils.AppiumServer import AppiumServer
test_ophone = []
def connectmobile() -> list:
    LOG.info("---开始链接stf平台-----")
    stf = StfPhoneOpear()
    all_list_phone = stf.getstflist()
    if len(all_list_phone)<Test_plan_num:
        return []
    LOG.info("---获取可用设备列表-----")
    for item in all_list_phone:
        if item['platform'] == Test_mobile_type and item['use'] is False:
            test_ophone.append(item)
    if len(test_ophone) < Test_plan_num:
        return []
    LOG.info("---准备申请设备-----")
    all_connect_phone = test_ophone[:Test_plan_num]
    connect_adb_device = []
    for i in all_connect_phone:
        LOG.info("---申请设备：%s-----"%i['serial'])
        stf.oparyonephone(i['serial'])
        LOG.info("---获取设备：%s 远程地址-----" % i['serial'])
        connect = stf.getoneconnecturl(i['serial'])
        all_detail = {}
        LOG.info("---链接设备：%s -----" % i['serial'])
        os.popen("/Users/lileilei/Downloads/android-sdk-macosx/platform-tools/adb connect %s" % connect)
        reslut = os.popen("/Users/lileilei/Downloads/android-sdk-macosx/platform-tools/adb devices").read()
        devices = str(reslut).split("\n")[1].split("\t")[0]
        all_detail['devices'] = devices
        all_detail['serial']=i['serial']
        all_detail['version'] = i['version']
        connect_adb_device.append(all_detail)
    return connect_adb_device


l_devices = []


def runnerPool(getDevices):
    '''
       根据链接的设备生成不同的dict
       然后放到设备的list里面
       设备list的长度产生进程池大小
    '''
    devices_Pool = []
    for i in range(0, len(getDevices)):
        _pool = []
        _initApp = {}
        _initApp["deviceName"] = getDevices[i]['devices']["devices"]
        _initApp["udid"] = getDevices[i]['devices']["devices"]
        _initApp["platformVersion"] = getDevices[i]['devices']['version']
        _initApp["platformName"] = Test_mobile_type
        _initApp["port"] = getDevices[i]["port"]
        _initApp["appPackage"] = TestappPackage
        _initApp["appActivity"] = TestAppActivity
        _pool.append(_initApp)
        devices_Pool.append(_initApp)
    pool = Pool(len(devices_Pool))
    pool.map(runnerCaseApp, devices_Pool)
    pool.close()
    pool.join()


def runnerCaseApp(devices):
    '''利用unittest的testsuite来组织测试用例'''
    test_suit = unittest.TestSuite()
    test_suit.addTest(Parmer.parametrize(regtest, param=devices))  # 扩展的其他的测试用例均这样添加
    unittest.TextTestRunner(verbosity=2).run(test_suit)
if __name__=="__main__":
    LOG.info("测试开始执行")
    start_time = datetime.datetime.now()
    makecasefile('reg', 'reg', 'reg')
    path = os.getcwd()
    filenm = path + '/testreport/' + 'result.xls'
    devicess=connectmobile()
    if len(devicess) > 0:
        for dev in devicess:
            app = {}
            app["devices"] = dev
            app["port"] = str(random.randint(4593, 4598))
            l_devices.append(app)
        appium_server = AppiumServer(l_devices)
        appium_server.start_server()#启动服务
        runnerPool(l_devices)
        try:
            appium_server.stop_server(devicess)
        except Exception as e:
            print("关闭服务失败，原因：%s"%e)
            LOG.info("关闭服务失败，原因：%s"%e)
        end_time=datetime.datetime.now()
        hour=end_time-start_time
        s=StfPhoneOpear()
        for i in devicess:
            LOG.info("---归还设备：%s -----" % i['serial'])
            s.removeroneophen(i["serial"])
        create(filename=filenm,devices_list=devicess,Test_version='2.0.1',testtime=str(hour))
        LOG.info("测试执行完毕，耗时：%s"%hour)
    else:
        LOG.info("没有可用的%s设备,请查看stf链接设备"%Test_mobile_type)
        print("没有可用的%s设备,请查看stf链接设备"%Test_mobile_type)

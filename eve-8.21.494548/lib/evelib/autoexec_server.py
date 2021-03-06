#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\eve\common\lib\autoexec_server.py
import autoexec_server_core
import log
import eveLog
startInline = ['config', 'dataconfig']
startServices = ['http',
 'cache',
 'i2',
 'languageSvc',
 'dogmaIM',
 'charMgr',
 'ship',
 'station',
 'beyonce',
 'keeper',
 'director',
 'factory',
 'standing2',
 'agentMgr',
 'LSC',
 'slash',
 'skillMgr',
 'corpStationMgr',
 'account',
 'petitioner',
 'watchdog',
 'lien',
 'effectCompiler',
 'billingMgr',
 'corpRegistry',
 'pathfinder',
 'allianceRegistry',
 'warRegistry',
 'onlineStatus',
 'market',
 'authentication',
 'emailreader',
 'dungeonExplorationMgr',
 'jumpCloneSvc',
 'jumpbeaconsvc',
 'facWarMgr',
 'damageTracker',
 'wormholeMgr',
 'infoGatheringMgr',
 'sovMgr',
 'communityClient',
 'mailMgr',
 'calendarMgr',
 'contactSvc',
 'notificationMgr',
 'voiceMgr',
 'voiceAdminMgr',
 'processHealth',
 'taleMgr',
 'taleDistributionMgr',
 'http',
 'http2',
 'sentinel',
 'securityMonitor',
 'battleInitialization',
 'vault',
 'dustEveChat',
 'dustSkill',
 'catmaStaticInfo',
 'districtSatelliteMgr',
 'districtLocation',
 'bountyMgr']
if prefs.GetValue('clusterMode', None) is not None and prefs.clusterMode != 'LIVE':
    startServices.append('localizationServer')
import eveLocalization
if boot.region == 'optic':
    eveLocalization.SetTimeDelta(28800)
autoexec_server_core.StartServer(startServices, startInline=startInline, serviceManagerClass='EveServiceManager')
#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/maps/mapSvc.py
import service
from service import SERVICE_START_PENDING, SERVICE_RUNNING
import blue
import telemetry
import form
import string
import trinity
import uthread
import util
import sys
from mapcommon import COLORCURVE_SECURITY, STARMAP_SCALE, SOLARSYSTEM_JUMP, JUMP_COLORS, LINESET_EFFECT
import mapcommon
import geo2
import cPickle
import log
import uiconst
import uicls
import searchUtil
TRANSLATETBL = '                               ! #$%&\\  ()*+,-./0123456789:;<=>?@abcdefghijklmnopqrstuvwxyz[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~                  \x91\x92             \xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbfaaaaaa\xc6ceeeeiiii\xd0nooooo\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdfaaaaaa\xe6ceeeeiiii\xf0nooooo\xf7ouuuuy\xfey'
SEC = 10000000L
MIN = SEC * 60L
HOUR = MIN * 60L
DAY = HOUR * 24L
WEEK = DAY * 7L
MONTH = WEEK * 4L
YEAR = DAY * 365L

class MapSvc(service.Service):
    __guid__ = 'svc.map'
    __notifyevents__ = ['OnSessionChanged']
    __servicename__ = 'map'
    __displayname__ = 'Map Client Service'
    __update_on_reload__ = 0
    __startupdependencies__ = ['settings']

    def Run(self, memStream = None):
        self.state = SERVICE_START_PENDING
        self.LogInfo('Starting Map Client Svc')
        self.GetMapCache()
        uicore.layer.starmap.Flush()
        self.Reset()
        self.state = SERVICE_RUNNING

    def Stop(self, memStream = None):
        if trinity.device is None:
            return
        self.LogInfo('Map svc')
        self.Reset()

    def OnSessionChanged(self, isRemote, sess, change):
        if 'charid' in change:
            self.__PurgeOldCachedMap2dData()

    def Reset(self):
        self.LogInfo('MapSvc Reset')
        self.securityInfo = None
        self.minimizedWindows = []
        self.activeMap = ''
        self.mapconnectionscache = None
        sm.ScatterEvent('OnMapReset')

    def Open(self):
        viewSvc = sm.GetService('viewState')
        if not viewSvc.IsViewActive('starmap', 'systemmap'):
            activeMap = settings.user.ui.Get('activeMap', 'starmap')
            viewSvc.ActivateView(activeMap)

    def GetActiveMapName(self):
        return settings.user.ui.Get('activeMap', 'starmap')

    def MinimizeWindows(self):
        lobby = form.Lobby.GetIfOpen()
        if lobby and not lobby.destroyed and lobby.state != uiconst.UI_HIDDEN and not lobby.IsMinimized() and not lobby.IsCollapsed():
            lobby.Minimize()
            self.minimizedWindows.append(form.Lobby.default_windowID)

    def ResetMinimizedWindows(self):
        if len(self.minimizedWindows) > 0:
            windowSvc = sm.GetService('window')
            for windowID in self.minimizedWindows:
                wnd = uicls.Window.GetIfOpen(windowID=windowID)
                if wnd and wnd.IsMinimized():
                    wnd.Maximize()

            self.minimizedWindows = []

    def Toggle(self, *args):
        viewSvc = sm.GetService('viewState').ToggleSecondaryView(self.GetActiveMapName())

    def ToggleMode(self, *args):
        viewSvc = sm.GetService('viewState')
        if viewSvc.IsViewActive('starmap'):
            viewSvc.ActivateView('systemmap')
        elif viewSvc.IsViewActive('systemmap'):
            viewSvc.ActivateView('starmap')

    def OpenMapsPalette(self):
        openMinimized = settings.user.ui.Get('MapWindowMinimized', False)
        form.MapsPalette.Open(openMinimized=openMinimized)

    def CloseMapsPalette(self):
        form.MapsPalette.CloseIfOpen()

    def GetSecColorList(self):
        return COLORCURVE_SECURITY

    def GetSecurityStatus(self, solarSystemID):
        if self.securityInfo is None:
            uthread.Lock(self)
            try:
                self.securityInfo = {}
                for each in cfg.solarsystems:
                    self.securityInfo[each.solarSystemID] = each.pseudoSecurity

            finally:
                uthread.UnLock(self)

        if solarSystemID in self.securityInfo:
            return util.FmtSystemSecStatus(self.securityInfo[solarSystemID])
        return 0.0

    def GetSecurityClass(self, solarSystemID):
        secLevel = self.GetSecurityStatus(solarSystemID)
        return util.SecurityClassFromLevel(secLevel)

    def CreateCacheFile(self):
        for language in [('EN', const.localizedLanguageEnglishUS), ('ZH', const.localizedLanguageChinese)]:
            self._CreateCacheFile(language)

    def _CreateCacheFile(self, language):
        languageID, numericLanguageID = language
        cache = {'items': {},
         'hierarchy': {},
         'neighbors': {},
         'parents': {},
         'children': {},
         'nodetype': {mapcommon.REGION_JUMP: [],
                      mapcommon.CONSTELLATION_JUMP: [],
                      mapcommon.SOLARSYSTEM_JUMP: []},
         'planets': {}}
        cacheItems = cache['items']
        cacheHierarchy = cache['hierarchy']
        cacheNeighbors = cache['neighbors']
        cacheParents = cache['parents']
        cacheChildren = cache['children']
        cacheNodeTypes = cache['nodetype']
        cachePlanets = cache['planets']
        configSvc = sm.RemoteSvc('config')
        regions = configSvc.CacheFileGetRegions(languageID)
        for region in regions:
            cacheHierarchy[region.itemID] = {}
            cacheItems[region.itemID] = util.KeyVal(__doc__='regionInfo', item=region, hierarchy=[region.itemID])
            cacheChildren[region.itemID] = []
            constellations = configSvc.CacheFileGetConstellations(languageID, region.itemID)
            for constellation in constellations:
                cacheChildren[region.itemID].append(constellation.itemID)
                cacheParents[constellation.itemID] = region.itemID
                cacheChildren[constellation.itemID] = []
                cacheHierarchy[region.itemID][constellation.itemID] = {}
                cacheItems[constellation.itemID] = util.KeyVal(__doc__='constellationInfo', item=constellation, hierarchy=[region.itemID, constellation.itemID])
                solarsystems = configSvc.CacheFileGetSystems(languageID, constellation.itemID)
                for solsys in solarsystems:
                    cacheChildren[constellation.itemID].append(solsys.itemID)
                    cacheParents[solsys.itemID] = constellation.itemID
                    cacheChildren[solsys.itemID] = []
                    cacheHierarchy[region.itemID][constellation.itemID][solsys.itemID] = []
                    cacheItems[solsys.itemID] = util.KeyVal(__doc__='solarSystemInfo', item=solsys, hierarchy=[region.itemID, constellation.itemID, solsys.itemID], jumps=([], [], []))

        sunTypeMap = configSvc.CacheFileGetSystemSunTypes()
        cache['sunTypes'] = sunTypeMap
        solarsystemconnections = configSvc.GetMapConnections(const.locationUniverse, 0, 0, 1)
        for connection in solarsystemconnections:
            ctype, fromreg, fromcon, fromsol, _id, __id, tosol, tocon, toreg = connection
            lst = cacheItems[fromsol].jumps
            fromRegObje = cacheItems[fromreg].item
            toRegObje = cacheItems[toreg].item
            if fromRegObje.itemName == '' or toRegObje.itemName == '':
                continue
            if fromreg != toreg:
                if tosol not in lst[mapcommon.REGION_JUMP]:
                    lst[mapcommon.REGION_JUMP].append(tosol)
            elif fromcon != tocon:
                if tosol not in lst[mapcommon.CONSTELLATION_JUMP]:
                    lst[mapcommon.CONSTELLATION_JUMP].append(tosol)
            elif tosol not in lst[mapcommon.SOLARSYSTEM_JUMP]:
                lst[mapcommon.SOLARSYSTEM_JUMP].append(tosol)
            if len(lst[mapcommon.SOLARSYSTEM_JUMP]):
                cacheNodeTypes[mapcommon.SOLARSYSTEM_JUMP].append(fromsol)
            elif len(lst[mapcommon.CONSTELLATION_JUMP]):
                cacheNodeTypes[mapcommon.CONSTELLATION_JUMP].append(fromsol)
            else:
                cacheNodeTypes[mapcommon.REGION_JUMP].append(fromsol)

        def AddConnectionToList(fromConn, toConn, theList):
            if fromConn not in theList:
                theList[fromConn] = [toConn]
            elif toConn not in theList[fromConn]:
                theList[fromConn].append(toConn)
            if toConn not in theList:
                theList[toConn] = [fromConn]
            elif fromConn not in theList[toConn]:
                theList[toConn].append(fromConn)
            return theList

        for connection in solarsystemconnections:
            ctype, fromreg, fromcon, fromsol, _id, __id, tosol, tocon, toreg = connection
            fromRegObje = cacheItems[fromreg].item
            toRegObje = cacheItems[toreg].item
            if fromRegObje.itemName == '' or toRegObje.itemName == '':
                continue
            if fromreg != toreg:
                AddConnectionToList(fromreg, toreg, cacheNeighbors)
            if fromcon != tocon:
                AddConnectionToList(fromcon, tocon, cacheNeighbors)

        landmarks = configSvc.CacheFileGetLandmarks()
        cacheLandmarks = cache['landmarks'] = {}
        for landmark in landmarks:
            cacheLandmarks[landmark.landmarkID] = util.KeyVal(__doc__='landmark', landmarkNameID=landmark.landmarkNameID, descriptionID=landmark.descriptionID, radius=landmark.radius, x=landmark.x, y=landmark.y, z=landmark.z, importance=landmark.importance, iconID=landmark.iconID)

        planetData = configSvc.CacheFileGetPlanetSolarSystemAndTypes()
        for row in planetData:
            cachePlanets[row.itemID] = (row.solarSystemID, row.typeID)

        self.mapcache = cache
        self.CreateSolarSystemJumps(cache, languageID)
        import os
        if languageID == 'EN':
            filename = os.path.join(blue.paths.ResolvePath(u'res:/'), 'UI/Shared/Maps/mapcache.dat')
        else:
            filename = os.path.join(blue.paths.ResolvePath(u'res:/'), 'UI/Shared/Maps/mapcache.%s.dat' % languageID)
        cacheStream = cPickle.dumps(cache)
        fileStream = file(filename, 'wb')
        fileStream.write(cacheStream)
        fileStream.close()

    def CreateJumpLines(self, listofIDs):
        lineID = 0
        constellationConnectionsMade = []
        linePointsToSet = []
        idToPointIDdict = {'jumpType': [[], [], []]}
        pointsAlreadySet = {0: {},
         1: {},
         2: {}}
        for fromID, toID, jumpType in listofIDs:
            solarsystem = self.GetItem(fromID)
            toitem = self.GetItem(toID)
            fromPos = geo2.Vector(solarsystem.x * STARMAP_SCALE, solarsystem.y * STARMAP_SCALE, solarsystem.z * STARMAP_SCALE)
            if jumpType == SOLARSYSTEM_JUMP:
                if (toID, fromID) in constellationConnectionsMade:
                    continue
            toPos = geo2.Vector(toitem.x * STARMAP_SCALE, toitem.y * STARMAP_SCALE, toitem.z * STARMAP_SCALE)
            direction = toPos - fromPos
            direction = geo2.Vector(*geo2.Vec3Normalize(direction)) * 8.0
            fromPos += direction
            toPos -= direction
            lineColor = JUMP_COLORS[jumpType]
            if jumpType == SOLARSYSTEM_JUMP:
                constellationConnectionsMade.append((fromID, toID))
            lineInfo = util.KeyVal(lineID=lineID, fromColor=list(lineColor), toColor=list(lineColor), fromID=fromID, toID=toID, jumpType=jumpType, fromPos=tuple(fromPos), toPos=tuple(toPos))
            linePointsToSet.append(lineInfo)
            if fromID not in idToPointIDdict:
                idToPointIDdict[fromID] = [(lineID, jumpType)]
            elif (lineID, jumpType) not in idToPointIDdict[fromID]:
                idToPointIDdict[fromID].append((lineID, jumpType))
            if toID not in idToPointIDdict:
                idToPointIDdict[toID] = [(lineID, jumpType)]
            elif (lineID, jumpType) not in idToPointIDdict[toID]:
                idToPointIDdict[toID].append((lineID, jumpType))
            idToPointIDdict[fromID, toID] = (lineID, fromID)
            idToPointIDdict[toID, fromID] = (lineID, fromID)
            idToPointIDdict['jumpType'][jumpType].append(lineID)
            lineID += 1

        idToPointIDdict['jumpLines'] = linePointsToSet
        return idToPointIDdict

    def CreateSolarSystemJumps(self, cache, scene, languageID = None):
        jumpsdone = []
        regionJumpDict = {}
        turrStart = blue.os.GetWallclockTimeNow()
        lineConnectionsToFeedFunction = []
        lineID = 0
        unconnectedSolarSystemIDs = []
        for regionID in [ regionID for regionID in cache['hierarchy'] if regionID < const.mapWormholeRegionMin ]:
            regionJumpDict[regionID] = []
            for constellationid in cache['hierarchy'][regionID].iterkeys():
                for solarSystemID in cache['hierarchy'][regionID][constellationid].iterkeys():
                    solarSystemInfo = cache['items'][solarSystemID]
                    solarsystem = solarSystemInfo.item
                    jumpType = 0
                    hasJumps = 0
                    for jumptypes in solarSystemInfo.jumps:
                        for jumplocation in jumptypes:
                            hasJumps = 1
                            if (solarsystem.itemID, jumplocation) in jumpsdone or (jumplocation, solarsystem.itemID) in jumpsdone:
                                continue
                            jumpsdone.append((solarsystem.itemID, jumplocation))
                            regionJumpDict[regionID].append((lineID, solarsystem.itemID))
                            lineID += 1
                            lineConnectionsToFeedFunction.append((solarsystem.itemID, jumplocation, jumpType))

                        jumpType += 1

                    if hasJumps == 0:
                        unconnectedSolarSystemIDs.append(solarSystemID)

        turrEnd = blue.os.GetWallclockTimeNow()
        self.LogInfo('MapSvc: Iterated through all jumps in', blue.os.TimeDiffInMs(turrStart, turrEnd), 'ms')
        solarSystemJumpIDdict = self.CreateJumpLines(lineConnectionsToFeedFunction)
        solarSystemJumpIDdict['regionJumpDict'] = regionJumpDict
        for regionID in self.GetSleeperspaceRegions():
            for constellationid in cache['hierarchy'][regionID].iterkeys():
                for solarSystemID in cache['hierarchy'][regionID][constellationid].iterkeys():
                    unconnectedSolarSystemIDs.append(solarSystemID)

        for solarSystemID in unconnectedSolarSystemIDs:
            solarSystemJumpIDdict[solarSystemID] = []

        cache['solarSystemJumpIDdict'] = solarSystemJumpIDdict

    @telemetry.ZONE_METHOD
    def GetMapCache(self):
        if not hasattr(self, 'mapcache') or self.mapcache is None:
            filename = 'res:/UI/Shared/Maps/mapcache.dat'
            f = blue.ResFile()
            if not f.Open(filename):
                raise RuntimeError('cant find the mapcache file')
            data = f.Read()
            blue.statistics.EnterZone('cPickle.loads')
            self.mapcache = cPickle.loads(data)
            blue.statistics.LeaveZone()
            f.Close()
            for locationID in self.mapcache['items']:
                self.mapcache['items'][locationID].item.itemName = cfg.evelocations.Get(locationID).name

        return self.mapcache

    @telemetry.ZONE_METHOD
    def GetSolarsystemItems(self, solarsystemID):
        local, playerStations = uthread.parallel([(cfg.GetLocationsLocalBySystem, (solarsystemID,)), (sm.RemoteSvc('config').GetDynamicCelestials, (solarsystemID,))], contextSuffix='GetSolarsystemItems')
        for station in playerStations:
            local.InsertNew(station)

        return local

    def __PurgeOldCachedMap2dData(self):
        try:
            settingKeys = settings.user.ui.GetValues()
            toRemove = []
            for key in settingKeys.keys():
                if isinstance(key, str) and key.startswith('map2d_'):
                    toRemove.append(key)

            for key in toRemove:
                settings.user.ui.Delete(key)
                log.LogInfo('Successfully removed old F11 map cache data: %s' % key)

        except:
            log.LogException('Failed to purge old map cache out of settings')

    def GetMapConnectionCache(self):
        if self.mapconnectionscache is None:
            self.mapconnectionscache = settings.user.ui.Get('map_cacheconnectionsfile', {})
        return self.mapconnectionscache or {}

    def GetItem(self, itemID, retall = False):
        if util.IsStation(itemID):
            station = cfg.stations.Get(itemID)
            return util.KeyVal(itemID=station.stationID, locationID=station.solarSystemID, itemName=cfg.evelocations.Get(itemID).name, typeID=station.stationTypeID, x=station.x, y=station.y, z=station.z)
        cache = self.GetMapCache()
        if 'items' not in cache:
            self.LogInfo('MapSvc: Error asking for item', itemID, ', there is no items entry in cache')
            return None
        if itemID in cache['items']:
            if retall:
                return cache['items'][itemID]
            else:
                return cache['items'][itemID].item

    def GetItemConnections(self, id, reg = 0, con = 0, sol = 0, cel = 0, _c = 0):
        if not isinstance(id, (int, long)):
            log.LogError('GetItemConnections supports only interger types, not', id.__class__.__name__, id)
            return
        retVal = None
        uthread.Lock('map_GetItemConnections')
        try:
            key = '%s_%s_%s_%s_%s_%s' % (id,
             reg,
             con,
             sol,
             cel,
             _c)
            cache = self.GetMapConnectionCache()
            if key not in cache:
                rec = sm.RemoteSvc('config').GetMapConnections(id, reg, con, sol, cel, _c)
                cache[key] = rec
                settings.user.ui.Set('map_cacheconnectionsfile', cache)
            retVal = cache[key]
        finally:
            uthread.UnLock('map_GetItemConnections')

        return retVal

    @telemetry.ZONE_METHOD
    def GetParentLocationID(self, locationID, gethierarchy = 0):
        cache = self.GetMapCache()
        for regionID in cache['hierarchy']:
            if locationID == regionID:
                if gethierarchy:
                    return (const.locationUniverse,
                     regionID,
                     None,
                     None,
                     None)
                return const.locationUniverse
            for constellationID in cache['hierarchy'][regionID]:
                if locationID == constellationID:
                    if gethierarchy:
                        return (const.locationUniverse,
                         regionID,
                         constellationID,
                         None,
                         None)
                    return regionID
                for solarsystemID in cache['hierarchy'][regionID][constellationID].iterkeys():
                    if locationID == solarsystemID:
                        if gethierarchy:
                            return (const.locationUniverse,
                             regionID,
                             constellationID,
                             solarsystemID,
                             None)
                        return constellationID
                    for itemID in cache['hierarchy'][regionID][constellationID][solarsystemID]:
                        if locationID == itemID:
                            if gethierarchy:
                                return (const.locationUniverse,
                                 regionID,
                                 constellationID,
                                 solarsystemID,
                                 itemID)
                            return solarsystemID

        if gethierarchy:
            return (const.locationUniverse,
             None,
             None,
             None,
             None)

    def FindByName(self, searchstr, ignorecommas = 1):
        match = []
        cache = self.GetMapCache()
        searchGroupList = [const.searchResultConstellation, const.searchResultSolarSystem, const.searchResultRegion]
        results = searchUtil.QuickSearch(searchstr, searchGroupList)
        for itemID in results:
            match.append(cache['items'][itemID].item)

        return match

    def GetLandmark(self, landmarkID):
        return self.GetMapCache()['landmarks'][landmarkID]

    def GetNeighbors(self, itemID):
        if util.IsWormholeSystem(itemID) or util.IsWormholeConstellation(itemID) or util.IsWormholeRegion(itemID):
            return []
        cache = self.GetMapCache()
        if itemID in cache['neighbors']:
            return cache['neighbors'][itemID]
        item = self.GetItem(itemID, 1)
        ssitem = item.item
        if ssitem.groupID == const.typeSolarSystem:
            return [ locID for jumpgroup in item.jumps for locID in jumpgroup ]
        else:
            return []

    def GetParent(self, itemID):
        item = self.GetItem(itemID)
        if item:
            return getattr(item, 'locationID', None) or const.locationUniverse

    def GetRegionForSolarSystem(self, solarSystemID):
        solarSystem = self.GetItem(solarSystemID)
        if not solarSystem:
            return None
        constellationID = solarSystem.locationID
        constellation = self.GetItem(constellationID)
        if constellation:
            return constellation.locationID

    def GetConstellationForSolarSystem(self, solarSystemID):
        solarSystem = self.GetItem(solarSystemID)
        if not solarSystem:
            return None
        return solarSystem.locationID

    def GetChildren(self, itemID):
        cache = self.GetMapCache()
        if itemID in cache['children']:
            return cache['children'][itemID]

    def ExpandItems(self, itemIDs):
        ret = []
        for i in itemIDs:
            if util.IsSolarSystem(i):
                ret.append(i)
            elif util.IsConstellation(i):
                ret.extend(self.GetChildren(i))
            elif util.IsRegion(i):
                for constellation in self.GetChildren(i):
                    ret.extend(self.GetChildren(constellation))

        return ret

    def GetKnownspaceRegions(self):
        cacheHierarchy = self.GetMapCache()['hierarchy']
        return [ regionID for regionID in cacheHierarchy if regionID < const.mapWormholeRegionMin ]

    def GetSleeperspaceRegions(self):
        cahceHierarchy = self.GetMapCache()['hierarchy']
        return [ regionID for regionID in cahceHierarchy if regionID >= const.mapWormholeRegionMin ]

    def GetNumberOfStargates(self, itemID):
        item = self.GetMapCache()['items'][itemID]
        return sum([ len(n) for n in item.jumps ])

    def GetSolasystemIDs(self, itemID = None):
        return [ systemID for systemID in self.IterateSolarSystemIDs(itemID) ]

    def IterateSolarSystemIDs(self, itemID = None):
        if itemID is None:
            for regionID in self.GetKnownspaceRegions():
                for constellationID in self.GetChildren(regionID):
                    for systemID in self.GetChildren(constellationID):
                        yield systemID

        elif util.IsSolarSystem(itemID):
            yield itemID
        elif util.IsConstellation(itemID):
            for systemID in self.GetChildren(itemID):
                yield systemID

        elif util.IsRegion(itemID):
            for constellationID in self.GetChildren(itemID):
                for systemID in self.GetChildren(constellationID):
                    yield systemID

    def GetPlanetInfo(self, planetID, hierarchy = False):
        solarSystemID, typeID = self.GetMapCache()['planets'][planetID]
        info = util.KeyVal(solarSystemID=solarSystemID, typeID=typeID)
        if hierarchy:
            regionID, constellationID, x = self.GetItem(solarSystemID, retall=True).hierarchy
            info.regionID = regionID
            info.constellationID = constellationID
        return info

    def IteratePlanetInfo(self):
        planetCache = self.GetMapCache()['planets']
        for planetID, (solarSystemID, typeID) in planetCache.iteritems():
            yield self.PlanetInfo(planetID, solarSystemID, typeID)

    def CreateLineSet(self, path = LINESET_EFFECT):
        lineSet = trinity.EveLineSet()
        lineSet.effect = trinity.Tr2Effect()
        lineSet.effect.effectFilePath = path
        lineSet.renderTransparent = False
        return lineSet

    def CreateCurvedLineSet(self, effectPath = None):
        lineSet = trinity.EveCurveLineSet()
        if effectPath is not None:
            lineSet.lineEffect.effectFilePath = effectPath
        texMap = trinity.TriTexture2DParameter()
        texMap.name = 'TexMap'
        texMap.resourcePath = 'res:/dx9/texture/UI/lineSolid.dds'
        lineSet.lineEffect.resources.append(texMap)
        overlayTexMap = trinity.TriTexture2DParameter()
        overlayTexMap.name = 'OverlayTexMap'
        overlayTexMap.resourcePath = 'res:/dx9/texture/UI/lineOverlay5.dds'
        lineSet.lineEffect.resources.append(overlayTexMap)
        return lineSet

    class PlanetInfo(object):
        __slots__ = ['planetID', 'solarSystemID', 'typeID']

        def __init__(self, planetID, solarSystemID, typeID):
            self.planetID = planetID
            self.solarSystemID = solarSystemID
            self.typeID = typeID

    def GetSystemColorString(self, solarSystemID):
        col = self.GetSystemColor(solarSystemID)
        return util.Color.RGBtoHex(col.r, col.g, col.b)

    def GetSystemColor(self, solarSystemID):
        sec, col = util.FmtSystemSecStatus(self.GetSecurityStatus(solarSystemID), 1)
        return col

    def GetStation(self, stationID):
        station = sm.RemoteSvc('stationSvc').GetStation(stationID)
        if cfg.IsLocalIdentity(stationID) and not station.conquerable:
            station.stationName = cfg.evelocations.Get(stationID).name
        return station
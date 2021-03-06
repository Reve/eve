#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/services/corporation/base_corporation.py
from service import SERVICE_START_PENDING, SERVICE_RUNNING, Service, ROLE_IGB, ROLE_ANY
import uix
import blue
import uthread
import util
import moniker
import corpObject
import uiconst
import localization
import form
import dbutil
import listentry
import corputil
import uicls
COMMUNICATIONS_OFFICER_ROLE_ID = 60217

def ReturnNone():
    return None


MAX_NUM_BULLETINS = 10

class Corporation(Service):
    __exportedcalls__ = {'AddCorporation': [],
     'GetCorporation': [],
     'GetDivisionNames': [],
     'GetCostForCreatingACorporation': [],
     'UpdateCorporationAbilities': [],
     'UpdateLogo': [],
     'UpdateCorporation': [],
     'GetSuggestedTickerNames': [],
     'GetSuggestedAllianceShortNames': [],
     'CreateAlliance': [],
     'ApplyToJoinAlliance': [],
     'GetAllianceApplications': [],
     'GetMemberIDs': [],
     'GetMembers': [],
     'GetMembersPaged': [],
     'GetMembersByIds': [],
     'GetMember': [],
     'GetMembersAsEveOwners': [],
     'GetMyGrantableRoles': [],
     'GetRoles': [],
     'GetRoleGroups': [],
     'GetLocationalRoles': [],
     'UpdateMember': [],
     'UpdateMembers': [],
     'UserIsActiveCEO': [],
     'UserIsCEO': [],
     'MemberCanCreateCorporation': [],
     'MemberCanRunForCEO': [],
     'CanKickOut': [],
     'KickOut': [],
     'RemoveAllRoles': [],
     'UserBlocksRoles': [],
     'GetMemberIDsWithMoreThanAvgShares': [],
     'GetMemberIDsByQuery': [],
     'ExecuteActions': [],
     'GetTitles': [],
     'UpdateTitle': [],
     'UpdateTitles': [],
     'DeleteTitle': [],
     'GetVoteCaseOptions': [],
     'CanViewVotes': [],
     'GetVoteCasesByCorporation': [],
     'GetSanctionedActionsByCorporation': [],
     'UpdateSanctionedAction': [],
     'InsertVoteCase': [],
     'GetVotes': [],
     'InsertVote': [],
     'CanVote': [],
     'ChangeMutualWarFlag': [],
     'GetRecentKills': [],
     'GetRecentLosses': [],
     'GetCorporationsWithOfficesAtStation': [],
     'GetOffices': [],
     'GetOffice': [],
     'GetOffice_NoWireTrip': [],
     'GetOfficeFolderIDForOfficeID': [],
     'RemoveOffice': [],
     'GetPublicStationInfo': [],
     'GetDivisionalRoles': [],
     'GetHierarchicalRoles': [],
     'GetApplications': [],
     'GetApplicationsWithStatus': [],
     'GetMyApplications': [],
     'GetMyApplicationsWithStatus': [],
     'InsertApplication': [],
     'ApplyForMembership': [],
     'GetCorpWelcomeMail': [],
     'SetCorpWelcomeMail': [],
     'GetActiveApplication': [],
     'UpdateApplicationOffer': [],
     'DoesCharactersCorpOwnThisStation': [],
     'MoveCompanyShares': [],
     'MovePrivateShares': [],
     'PayoutDividend': [],
     'UpdateDivisionNames': [],
     'ResignFromCEO': [],
     'GetInfoWindowDataForChar': [],
     'GetMemberTrackingInfo': [],
     'GetRentalDetailsPlayer': [],
     'GetRentalDetailsCorp': [],
     'GetLockedItemsByLocation': [],
     'GetLockedItemLocations': [],
     'IsItemLocked': [],
     'IsItemIDLocked': [],
     'GetCorpStationManager': [],
     'SetAccountKey': [],
     'GetMyCorpAccountName': [],
     'GetRecruitmentAdTypes': [],
     'EditBulletin': [ROLE_IGB | ROLE_ANY],
     'DeleteBulletin': [ROLE_IGB],
     'GetContactList': [],
     'LogCorpRecruitmentEvent': []}
    __guid__ = 'svc.corp'
    __notifyevents__ = ['DoSessionChanging',
     'OnSessionChanged',
     'OnCorporationChanged',
     'OnOfficeRentalChanged',
     'OnCorporationMemberChanged',
     'OnCorporationVoteCaseChanged',
     'OnCorporationVoteCaseOptionChanged',
     'OnCorporationVoteChanged',
     'OnSanctionedActionChanged',
     'OnCorporationApplicationChanged',
     'OnCorporationRecruitmentAdChanged',
     'OnShareChange',
     'OnGodmaSkillTrained',
     'OnAttribute',
     'OnTitleChanged',
     'OnAllianceApplicationChanged',
     'OnLockedItemChange',
     'OnCorporationWelcomeMailChanged']
    __servicename__ = 'corp'
    __displayname__ = 'Corporation Client Service'
    __dependencies__ = []
    __functionalobjects__ = ['corporations',
     'members',
     'applications',
     'shares',
     'voting',
     'sanctionedActions',
     'alliance',
     'locations',
     'titles',
     'itemLocking',
     'wars',
     'recruitment']

    def __init__(self):
        Service.__init__(self)
        self.__roles = None
        self.__roleGroups = None
        self.__roleGroupings = None
        self.__roleGroupingsForTitles = None
        self.__divisionalRoles = None
        self.__hierarchicalRoles = None
        self.__locationalRoles = [const.corpRoleHangarCanTake1,
         const.corpRoleHangarCanTake2,
         const.corpRoleHangarCanTake3,
         const.corpRoleHangarCanTake4,
         const.corpRoleHangarCanTake5,
         const.corpRoleHangarCanTake6,
         const.corpRoleHangarCanTake7,
         const.corpRoleHangarCanQuery1,
         const.corpRoleHangarCanQuery2,
         const.corpRoleHangarCanQuery3,
         const.corpRoleHangarCanQuery4,
         const.corpRoleHangarCanQuery5,
         const.corpRoleHangarCanQuery6,
         const.corpRoleHangarCanQuery7,
         const.corpRoleContainerCanTake1,
         const.corpRoleContainerCanTake2,
         const.corpRoleContainerCanTake3,
         const.corpRoleContainerCanTake4,
         const.corpRoleContainerCanTake5,
         const.corpRoleContainerCanTake6,
         const.corpRoleContainerCanTake7]
        self.__recruitmentAdTypes = None
        self.__recruitmentAdGroups = None
        self.hasImpoundedItemsCache = None
        self.hasImpoundedItemsCacheTime = None
        self.resigning = False

    def GetDependencies(self):
        return self.__dependencies__

    def GetObjectNames(self):
        return self.__functionalobjects__

    def Run(self, memStream = None):
        self.LogInfo('Starting Corporation')
        self.state = SERVICE_START_PENDING
        sm.FavourMe(self.OnSessionChanged)
        sm.FavourMe(self.OnOfficeRentalChanged)
        sm.FavourMe(self.OnCorporationMemberChanged)
        self.__corpRegistry = None
        self.__corpRegistryCorpID = None
        self.__corpStationManager = None
        self.__corpStationManagerStationID = None
        items = corpObject.__dict__.items()
        for objectName in self.__functionalobjects__:
            if objectName == 'base':
                continue
            object = None
            classType = 'corpObject.%s' % objectName
            for i in range(0, len(corpObject.__dict__)):
                self.LogInfo('Processing', items[i])
                if len(items[i][0]) > 1:
                    if items[i][0][:2] == '__':
                        continue
                if items[i][1].__guid__ == classType:
                    object = CreateInstance(classType, (self,))
                    break

            if object is None:
                raise RuntimeError('FunctionalObject not found %s' % classType)
            setattr(self, objectName, object)

        for objectName in self.__functionalobjects__:
            object = getattr(self, objectName)
            object.DoObjectWeakRefConnections()

        self.state = SERVICE_RUNNING
        if eve.session.corpid:
            uthread.new(self.members.PrimeCorpInformation)
            if not util.IsNPC(eve.session.corpid):
                uthread.new(self.GetMyCorporationsOffices)
        self.bulletins = None
        self.bulletinsTimestamp = 0

    def Stop(self, memStream = None):
        self.__corpRegistry = None
        self.__corpRegistryCorpID = None
        self.__corpStationManager = None
        self.__corpStationManagerStationID = None

    def RefreshMoniker(self):
        if self.__corpRegistry is not None:
            self.__corpRegistry.UnBind()

    def GetCorpRegistry(self):
        if self.__corpRegistry is None:
            self.__corpRegistry = moniker.GetCorpRegistry()
            self.__corpRegistryCorpID = eve.session.corpid
        if self.__corpRegistryCorpID != eve.session.corpid:
            if self.__corpRegistry is not None:
                self.__corpRegistry.Unbind()
            self.__corpRegistry = moniker.GetCorpRegistry()
            self.__corpRegistryCorpID = eve.session.corpid
        return self.__corpRegistry

    def GetCorpStationManager(self):
        if not eve.session.stationid2:
            if self.__corpStationManager is not None:
                self.__corpStationManager.Unbind()
            raise RuntimeError('InvalidCallee due to state')
        else:
            if self.__corpStationManager is None:
                self.__corpStationManager = moniker.GetCorpStationManager()
                self.__corpStationManagerStationID = eve.session.stationid2
            if self.__corpStationManagerStationID != eve.session.stationid2:
                if self.__corpStationManager is not None:
                    self.__corpStationManager.Unbind()
                self.__corpStationManager = moniker.GetCorpStationManager()
                self.__corpStationManagerStationID = eve.session.stationid2
        return self.__corpStationManager

    def HasCorpImpoundedItemsAtStation(self):
        if self.hasImpoundedItemsCacheTime and blue.os.TimeDiffInMs(self.hasImpoundedItemsCacheTime, blue.os.GetTime()) < 60000:
            return self.hasImpoundedItemsCache
        corpStationMgr = self.GetCorpStationManager()
        if corpStationMgr and corpStationMgr.DoesPlayersCorpHaveJunkAtStation():
            self.hasImpoundedItemsCache = True
        else:
            self.hasImpoundedItemsCache = False
        self.hasImpoundedItemsCacheTime = blue.os.GetTime()
        return self.hasImpoundedItemsCache

    def PerformSelectiveSessionChange(self, reason, func, *args, **keywords):
        violateSafetyTimer = 0
        if session.nextSessionChange is not None and session.nextSessionChange > blue.os.GetSimTime():
            if session.sessionChangeReason == reason:
                violateSafetyTimer = 1
        if violateSafetyTimer > 0:
            print 'I will perform a session change even though I should wait %d more seconds' % ((session.nextSessionChange - blue.os.GetSimTime()) / SEC)
        import copy
        kw2 = copy.copy(keywords)
        kw2['violateSafetyTimer'] = violateSafetyTimer
        kw2['wait'] = 1
        sm.StartService('sessionMgr').PerformSessionChange(reason, func, *args, **kw2)

    def SetAccountKey(self, accountKey):
        self.PerformSelectiveSessionChange('corp.setaccountkey', self.members.SetAccountKey, accountKey)

    def GetCorpAccountName(self, acctID):
        if acctID is None:
            return
        return self.GetDivisionNames()[acctID - 1000 + 8]

    def GetMyCorpAccountName(self):
        return eve.session.corpAccountKey and self.GetCorpAccountName(eve.session.corpAccountKey)

    def CallDelegates(self, functionName, *args):
        for objectName in self.__functionalobjects__:
            object = getattr(self, objectName)
            function = getattr(object, functionName, None)
            if function is not None:
                function(*args)

    def DoSessionChanging(self, isRemote, session, change):
        if 'stationid2' in change:
            oldID, newID = change['stationid2']
            if self.__corpStationManager is not None:
                self.__corpStationManager = None
                self.__corpStationManagerStationID = None
        if 'corpid' in change:
            self.__hierarchicalRoles = None
            self.__divisionalRoles = None
            self.__roleGroupings = None
            self.__roleGroupingsForTitles = None
        self.CallDelegates('DoSessionChanging', isRemote, session, change)
        if 'charid' in change and change['charid'][0] or 'userid' in change and change['userid'][0]:
            sm.StopService(self.__guid__[4:])

    def OnSessionChanged(self, isRemote, session, change):
        self.CallDelegates('OnSessionChanged', isRemote, session, change)
        if 'corpid' in change:
            self.bulletins = None
            self.bulletinsTimestamp = 0

    def GetCorporation(self, corpid = None, new = 0):
        return self.corporations.GetCorporation(corpid, new)

    def GetCostForCreatingACorporation(self):
        return self.corporations.GetCostForCreatingACorporation()

    def UpdateCorporationAbilities(self):
        return self.corporations.UpdateCorporationAbilities()

    def UpdateLogo(self, shape1, shape2, shape3, color1, color2, color3, typeface):
        return self.corporations.UpdateLogo(shape1, shape2, shape3, color1, color2, color3, typeface)

    def UpdateCorporation(self, description, url, taxRate, acceptApplications):
        return self.corporations.UpdateCorporation(description, url, taxRate, acceptApplications)

    def GetSuggestedTickerNames(self, corporationName):
        return self.corporations.GetSuggestedTickerNames(corporationName)

    def AddCorporation(self, corporationName, tickerName, description, url = '', taxRate = 0.0, shape1 = None, shape2 = None, shape3 = None, color1 = None, color2 = None, color3 = None, typeface = None, applicationsEnabled = 1):
        return self.corporations.AddCorporation(corporationName, tickerName, description, url, taxRate, shape1, shape2, shape3, color1, color2, color3, typeface, applicationsEnabled)

    def OnCorporationChanged(self, corpID, change):
        self.corporations.OnCorporationChanged(corpID, change)

    def GetDivisionNames(self, new = 0):
        names = self.corporations.GetDivisionNames(new)
        return names

    def GetSuggestedAllianceShortNames(self, allianceName):
        return self.alliance.GetSuggestedAllianceShortNames(allianceName)

    def CreateAlliance(self, allianceName, shortName, description, url):
        return self.alliance.CreateAlliance(allianceName, shortName, description, url)

    def ApplyToJoinAlliance(self, allianceID, applicationText):
        return self.alliance.ApplyToJoinAlliance(allianceID, applicationText)

    def GetAllianceApplications(self):
        return self.alliance.GetAllianceApplications()

    def DeleteAllianceApplication(self, allianceID):
        return self.alliance.DeleteAllianceApplication(allianceID)

    def OnAllianceApplicationChanged(self, allianceID, corpID, change):
        if corpID == eve.session.corpid:
            self.alliance.OnAllianceApplicationChanged(allianceID, corpID, change)

    def GetMemberIDs(self):
        return self.members.GetMemberIDs()

    def GetMembers(self):
        return self.members.GetMembers()

    def GetMembersPaged(self, page):
        return self.members.GetMembersPaged(page)

    def GetMembersByIds(self, memberIDs):
        return self.members.GetMembersByIds(memberIDs)

    def GetMember(self, charID):
        return self.members.GetMember(charID)

    def GetMembersAsEveOwners(self):
        return self.members.GetMembersAsEveOwners()

    def UpdateMember(self, charIDToUpdate, title = None, divisionID = None, squadronID = None, roles = None, grantableRoles = None, rolesAtHQ = None, grantableRolesAtHQ = None, rolesAtBase = None, grantableRolesAtBase = None, rolesAtOther = None, grantableRolesAtOther = None, baseID = None, titleMask = None, blockRoles = None):
        return self.members.UpdateMember(charIDToUpdate, title, divisionID, squadronID, roles, grantableRoles, rolesAtHQ, grantableRolesAtHQ, rolesAtBase, grantableRolesAtBase, rolesAtOther, grantableRolesAtOther, baseID, titleMask, blockRoles)

    def UpdateMembers(self, rows):
        return self.members.UpdateMembers(rows)

    def OnCorporationMemberChanged(self, memberID, change):
        self.members.OnCorporationMemberChanged(memberID, change)

    def UserIsCEO(self):
        return self.GetCorporation().ceoID == eve.session.charid

    def UserIsActiveCEO(self):
        if eve.session.corprole & const.corpRoleDirector:
            if self.UserIsCEO():
                return 1
        return 0

    def MemberCanRunForCEO(self):
        return self.members.MemberCanRunForCEO()

    def MemberCanCreateCorporation(self):
        return self.members.MemberCanCreateCorporation()

    def GetMyGrantableRoles(self):
        return self.members.GetMyGrantableRoles()

    def CanLeaveCurrentCorporation(self):
        return self.GetCorpRegistry().CanLeaveCurrentCorporation()

    def CanKickOut(self, charID):
        if eve.session.charid != charID and const.corpRoleDirector & eve.session.corprole != const.corpRoleDirector:
            return 0
        return self.GetCorpRegistry().CanBeKickedOut(charID)

    def KickOut(self, charID, confirm = True):
        if not self.CanKickOut(charID):
            raise UserError('CrpAccessDenied', {'reason': localization.GetByLabel('UI/Corporations/BaseCorporationUI/CannotKickMember')})
        warEntityID = session.allianceid or session.corpid
        activeWars = []
        for war in sm.GetService('war').GetWars(warEntityID).itervalues():
            if war.mutual:
                continue
            if war.timeFinished is not None:
                continue
            activeWars.append(war)

        if activeWars:
            if eve.Message('CorpMemberKickActiveWarConfirm', {'noOfWars': len(activeWars),
             'character': charID}, uiconst.YESNO) != uiconst.ID_YES:
                return
        if self.resigning:
            return
        try:
            self.resigning = True
            if confirm:
                if charID == eve.session.charid:
                    if eve.Message('ConfirmQuitCorporation', {}, uiconst.OKCANCEL) != uiconst.ID_OK:
                        return
                elif eve.Message('ConfirmKickCorpMember', {'member': charID}, uiconst.OKCANCEL) != uiconst.ID_OK:
                    return
        finally:
            self.resigning = False

        res = None
        if charID == eve.session.charid:
            sm.GetService('sessionMgr').PerformSessionChange('corp.kickself', self.GetCorpRegistry().KickOutMember, charID)
        else:
            res = self.GetCorpRegistry().KickOutMember(charID)
        return res

    def RemoveAllRoles(self, silent = False):
        if not silent and eve.Message('ConfirmRemoveAllRoles', {}, uiconst.OKCANCEL) != uiconst.ID_OK:
            return
        self.UpdateMember(eve.session.charid, None, None, None, 0, 0, 0, 0, 0, 0, 0, 0, None, 0, 1)

    def GetMemberIDsWithMoreThanAvgShares(self):
        return self.GetCorpRegistry().GetMemberIDsWithMoreThanAvgShares()

    def GetMemberIDsByQuery(self, query, includeImplied, searchTitles):
        return self.GetCorpRegistry().GetMemberIDsByQuery(query, includeImplied, searchTitles)

    def ExecuteActions(self, targetIDs, actions):
        return self.members.ExecuteActions(targetIDs, actions)

    def OnGodmaSkillTrained(self, skillID):
        self.members.OnGodmaSkillTrained(skillID)

    def OnAttribute(self, attributeName, item, value):
        self.members.OnAttribute(attributeName, item, value)

    def OnAttributes(self, changes):
        self.members.OnAttributes(changes)

    def UserBlocksRoles(self):
        return self.members.MemberBlocksRoles()

    def GetTitles(self):
        return self.titles.GetTitles()

    def UpdateTitle(self, titleID, titleName, roles, grantableRoles, rolesAtHQ, grantableRolesAtHQ, rolesAtBase, grantableRolesAtBase, rolesAtOther, grantableRolesAtOther):
        self.titles.UpdateTitle(titleID, titleName, roles, grantableRoles, rolesAtHQ, grantableRolesAtHQ, rolesAtBase, grantableRolesAtBase, rolesAtOther, grantableRolesAtOther)

    def UpdateTitles(self, titles):
        self.titles.UpdateTitles(titles)

    def DeleteTitle(self, titleID):
        self.titles.DeleteTitle(titleID)

    def OnTitleChanged(self, corpID, titleID, change):
        self.titles.OnTitleChanged(corpID, titleID, change)

    def GetSharesByShareholder(self, corpShares = 0):
        return self.shares.GetSharesByShareholder(corpShares)

    def GetShareholders(self):
        return self.shares.GetShareholders()

    def MoveCompanyShares(self, corporationID, toShareholderID, numberOfShares):
        return self.shares.MoveCompanyShares(corporationID, toShareholderID, numberOfShares)

    def MovePrivateShares(self, corporationID, toShareholderID, numberOfShares):
        return self.shares.MovePrivateShares(corporationID, toShareholderID, numberOfShares)

    def OnShareChange(self, shareholderID, corporationID, change):
        self.shares.OnShareChange(shareholderID, corporationID, change)
        self.members.OnShareChange(shareholderID, corporationID, change)
        self.voting.OnShareChange(shareholderID, corporationID, change)

    def GetVoteCasesByCorporation(self, corpid, new = 0, maxLen = 0):
        return self.voting.GetVoteCasesByCorporation(corpid, new, maxLen)

    def GetVoteCaseOptions(self, voteID, corpID = None):
        return self.voting.GetVoteCaseOptions(voteID, corpID)

    def OnCorporationVoteCaseChanged(self, corporationID, voteCaseID, change):
        self.voting.OnCorporationVoteCaseChanged(corporationID, voteCaseID, change)

    def OnCorporationVoteCaseOptionChanged(self, corporationID, voteCaseID, optionID, change):
        self.voting.OnCorporationVoteCaseOptionChanged(corporationID, voteCaseID, optionID, change)

    def OnCorporationVoteChanged(self, corporationID, voteCaseID, characterID, change):
        self.voting.OnCorporationVoteChanged(corporationID, voteCaseID, characterID, change)

    def CanViewVotes(self, corpid, new = 0):
        return self.voting.CanViewVotes(corpid, new)

    def GetSanctionedActionsByCorporation(self, corporationID, state):
        return self.sanctionedActions.GetSanctionedActionsByCorporation(corporationID, state)

    def UpdateSanctionedAction(self, voteCaseID, inEffect, reason = ''):
        return self.sanctionedActions.UpdateSanctionedAction(voteCaseID, inEffect, reason)

    def OnSanctionedActionChanged(self, corpID, voteCaseID, change):
        return self.sanctionedActions.OnSanctionedActionChanged(corpID, voteCaseID, change)

    def InsertVoteCase(self, voteCaseText, description, corporationID, voteType, voteCaseOptions, startDateTime = None, endDateTime = None):
        return self.voting.InsertVoteCase(voteCaseText, description, corporationID, voteType, voteCaseOptions, startDateTime, endDateTime)

    def GetVotes(self, corporationID, voteCaseID):
        return self.voting.GetVotes(corporationID, voteCaseID)

    def InsertVote(self, corporationID, voteCaseID, voteValue):
        return self.voting.InsertVote(corporationID, voteCaseID, voteValue)

    def CanVote(self, corporationID):
        return self.voting.CanVote(corporationID)

    def DeclareWarAgainst(self, againstID, cost):
        return moniker.GetCorpRegistry().DeclareWarAgainst(againstID, cost)

    def ChangeMutualWarFlag(self, warID, mutual):
        return self.wars.ChangeMutualWarFlag(warID, mutual)

    def GetRecentKills(self, num, offset):
        return self.wars.GetRecentKills(num, offset)

    def GetRecentLosses(self, num, offset):
        return self.wars.GetRecentLosses(num, offset)

    def OnCorporationApplicationChanged(self, corpID, applicantID, applicationID, newApplication):
        self.applications.OnCorporationApplicationChanged(corpID, applicantID, applicationID, newApplication)

    def GetApplications(self, characterID = -1, forceUpdate = False):
        return self.applications.GetApplications(characterID, forceUpdate)

    def GetApplicationsWithStatus(self, status):
        return self.applications.GetApplicationsWithStatus(status)

    def GetOldApplicationsWithStatus(self, status):
        return self.applications.GetOldApplicationsWithStatus(status)

    def GetMyApplications(self, corporationID = -1, forceUpdate = False):
        return self.applications.GetMyApplications(corporationID, forceUpdate)

    def GetMyApplicationsWithStatus(self, status):
        return self.applications.GetMyApplicationsWithStatus(status)

    def GetMyOldApplicationsWithStatus(self, status):
        return self.applications.GetMyOldApplicationsWithStatus(status)

    def InsertApplication(self, corporationID, applicationText):
        return self.applications.InsertApplication(corporationID, applicationText)

    def UpdateApplicationOffer(self, applicationID, characterID, corporationID, applicationText, status, applicationDateTime = None):
        return self.applications.UpdateApplicationOffer(applicationID, characterID, corporationID, applicationText, status, applicationDateTime)

    def GetActiveApplication(self, corpid):
        applications = self.GetMyApplications(corpid)
        for application in applications:
            if application.status in [const.crpApplicationAcceptedByCorporation, const.crpApplicationAppliedByCharacter]:
                return application

    def ApplyForMembership(self, corpid):
        if not eve.session.stationid2:
            raise UserError('CanNotApplyToCorpUnlessDocked')
        if eve.session.corpid == corpid:
            raise UserError('CanNotJoinCorpAlreadyAMember', {'corpName': cfg.eveowners.Get(eve.session.corpid).name})
        if self.UserIsCEO():
            raise UserError('CeoCanNotJoinACorp', {'CEOsCorporation': cfg.eveowners.Get(eve.session.corpid).name,
             'otherCorporation': cfg.eveowners.Get(corpid).name})
        application = self.GetActiveApplication(corpid)
        if application is not None:
            wnd = form.MyCorpApplicationWnd.Open(corpid=application.corporationID, application=application, status=application.status)
            if wnd.ShowModal() == 1:
                retval = wnd.result
            else:
                retval = None
            if retval is not None:
                sm.GetService('corp').UpdateApplicationOffer(application.applicationID, application.characterID, application.corporationID, application.applicationText, retval)
            return
        corporation = self.GetCorporation(corpid)
        wnd = form.ApplyToCorpWnd.Open(corpid=corpid, corporation=corporation)
        if wnd.ShowModal() == 1:
            retval = wnd.result
        else:
            retval = None
        if retval is not None:
            return self.InsertApplication(corpid, retval)

    def CheckApplication(self, retval):
        if retval.has_key('appltext'):
            applicationText = retval['appltext']
            if len(applicationText) > 1000:
                return localization.GetByLabel('UI/Corporations/BaseCorporationUI/ApplicationTextTooLong', length=len(applicationText))
        return ''

    def GetCorpWelcomeMail(self):
        return self.applications.GetCorpWelcomeMail()

    def SetCorpWelcomeMail(self, welcomeMail):
        self.GetCorpRegistry().SetCorpWelcomeMail(welcomeMail)

    def OnCorporationWelcomeMailChanged(self, characterID, changeDate):
        self.applications.SetCorpWelcomeMail(None)

    def GetPublicStationInfo(self):
        return self.locations.GetPublicStationInfo()

    def GetCorporationsWithOfficesAtStation(self):
        return self.locations.GetCorporationsWithOfficesAtStation()

    def GetOffices(self):
        return self.locations.GetOffices()

    def GetOffice(self, corpID = None):
        return self.locations.GetOffice(corpID)

    def GetOffice_NoWireTrip(self):
        return self.locations.GetOffice_NoWireTrip()

    def GetOfficeFolderIDForOfficeID(self, officeID):
        return self.locations.GetOfficeFolderIDForOfficeID(officeID)

    def AddOffice(self, corporationID, officeID, folderID):
        return self.locations.AddOffice(corporationID, officeID, folderID)

    def RemoveOffice(self, corporationID, officeID, folderID):
        return self.locations.RemoveOffice(corporationID, officeID, folderID)

    def OnOfficeRentalChanged(self, corporationID, officeID, folderID):
        self.locations.OnOfficeRentalChanged(corporationID, officeID, folderID)

    def DoesCharactersCorpOwnThisStation(self):
        return self.locations.DoesCharactersCorpOwnThisStation()

    def GetMyCorporationsOffices(self):
        return self.locations.GetMyCorporationsOffices()

    def GetMyCorporationsStations(self):
        return self.locations.GetMyCorporationsStations()

    def OnCorporationRecruitmentAdChanged(self):
        self.recruitment.OnCorporationRecruitmentAdChanged()

    def CreateRecruitmentAd(self, days, typeMask, langMask, description = None, channelID = None, recruiters = (), title = None, hourMask1 = 0, hourMask2 = 0):
        return sm.ProxySvc('corpRecProxy').CreateRecruitmentAd(days, typeMask, langMask, description, channelID, recruiters, title, hourMask1, hourMask2)

    def UpdateRecruitmentAd(self, adID, typeMask, langMask, description = None, channelID = None, recruiters = (), title = None, addedDays = 0, hourMask1 = 0, hourMask2 = 0):
        return sm.ProxySvc('corpRecProxy').UpdateRecruitmentAd(adID, typeMask, langMask, description, channelID, recruiters, title, addedDays, hourMask1, hourMask2)

    def DeleteRecruitmentAd(self, adID):
        return sm.ProxySvc('corpRecProxy').DeleteRecruitmentAd(adID)

    def GetRecruitmentAdsForCorporation(self):
        return self.recruitment.GetRecruitmentAdsForCorporation()

    def GetRecruitmentAdsForCorpID(self, corpID):
        return sm.ProxySvc('corpRecProxy').GetRecruitmentAdsByCorpID(corpID)

    def GetRecruiters(self, adID):
        return sm.ProxySvc('corpRecProxy').GetRecruiters(adID)

    def GetRecruitmentAdsByCriteria(self, typeMask, langMask, excludeAlliances, minMembers, maxMembers, searchTimeMask):
        return sm.ProxySvc('corpRecProxy').SearchCorpAds(typeMask, langMask, excludeAlliances, minMembers, maxMembers, searchTimeMask)

    def GetAdFromCorpAndAdID(self, corpID, adID):
        return sm.ProxySvc('corpRecProxy').GetRecruitmentAd(corpID, adID)

    def GetDivisionalRoles(self):
        if self.__divisionalRoles is None:
            roles = self.GetHierarchicalRoles()
            divisions = roles.divisions
            self.__divisionalRoles = []
            for divisionNumber, division in divisions.iteritems():
                for role in division.roles.itervalues():
                    self.__divisionalRoles.append(role.roleID)

        return self.__divisionalRoles

    def GetHierarchicalRoles(self):
        if self.__hierarchicalRoles is None:
            divisionNames = self.GetDivisionNames()
            roles = self.GetRoles()
            divisions = {}
            general = util.Rowset(roles.columns)
            digits = ('1', '2', '3', '4', '5', '6', '7')
            for role in roles:
                lastCharacter = role.roleName[-1:]
                if lastCharacter not in digits:
                    general.append(util.Row(roles.header, role))
                else:
                    divisionID = int(lastCharacter)
                    if not divisions.has_key(divisionID):
                        divisions[divisionID] = util.Row(['name', 'roles'], [divisionNames[divisionID], {}])
                    divisions[divisionID].roles[role.roleName[:-1]] = role

            self.__hierarchicalRoles = util.Row(['general', 'divisions'], [general, divisions])
        return self.__hierarchicalRoles

    def GetRoles(self):
        if self.__roles is None:
            roles = self.GetCorpRegistry().GetRoles()
            roleRowDesc = blue.DBRowDescriptor((('roleIID', const.DBTYPE_I4),
             ('roleID', const.DBTYPE_I8),
             ('roleName', const.DBTYPE_WSTR),
             ('shortDescription', const.DBTYPE_WSTR),
             ('description', const.DBTYPE_WSTR)))
            self.__roles = dbutil.CRowset(roleRowDesc, [])
            for row in roles:
                shortDescription = localization.GetByMessageID(row.shortDescriptionID)
                description = localization.GetByMessageID(row.descriptionID)
                self.__roles.InsertNew([row.roleIID,
                 row.roleID,
                 row.roleName,
                 shortDescription,
                 description])

        return self.__roles

    def GetRoleGroups(self):
        if self.__roleGroups is None:
            self.__roleGroups = self.GetCorpRegistry().GetRoleGroups()
        return self.__roleGroups

    def GetRoleGroupings(self, forTitles = 0):
        roleGroups = self.GetRoleGroups()
        divisionNames = self.GetDivisionNames()
        roles = self.GetRoles()
        header = None
        lines = []
        for roleGroup in roleGroups:
            line = []
            if header is None:
                header = []
                for columnName in roleGroups.columns:
                    header.append(columnName)

                header.append('columns')
            for columnName in header:
                if columnName == 'columns':
                    continue
                s = getattr(roleGroup, columnName)
                line.append(s)

            columns = []
            if roleGroup.isDivisional:
                rolesByDivisions = {}
                isAccount = False
                for role in roles:
                    if role.roleID & roleGroup.roleMask == role.roleID:
                        divisionID = int(role.roleName[-1:])
                        if not rolesByDivisions.has_key(divisionID):
                            rolesByDivisions[divisionID] = []
                        desc = ''
                        if -1 != role.roleName.find('CanTake'):
                            desc = localization.GetByLabel('UI/Corporations/BaseCorporationUI/Take')
                        elif -1 != role.roleName.find('CanQuery'):
                            desc = localization.GetByLabel('UI/Corporations/BaseCorporationUI/Query')
                        if role.roleName.startswith('roleAccount'):
                            isAccount = True
                            desc = ''
                        rolesByDivisions[divisionID].append([role.roleName, [desc, role]])

                for divisionID in (1, 2, 3, 4, 5, 6, 7):
                    subcolumns = []
                    rolesByDivision = rolesByDivisions[divisionID]
                    rolesByDivision.sort(lambda a, b: -(a[1][0].upper() < b[1][0].upper()))
                    for roleName, descAndRole in rolesByDivision:
                        subcolumns.append(descAndRole)

                    add = [0, 7][isAccount]
                    name = divisionNames.get(divisionID + add, None)
                    columns.append([name, subcolumns])

            else:

                def SortKey(a, b):
                    return -(a.shortDescription.upper() < b.shortDescription.upper())

                roles.sort(SortKey)
                for role in roles:
                    if forTitles and role.roleID == const.corpRoleDirector:
                        continue
                    if role.roleID & roleGroup.roleMask == role.roleID:
                        columns.append([role.shortDescription, [['', role]]])

            line.append(columns)
            lines.append(line)

        if forTitles:
            self.__roleGroupingsForTitles = util.IndexRowset(header, lines, 'roleGroupID')
            return self.__roleGroupingsForTitles
        else:
            self.__roleGroupings = util.IndexRowset(header, lines, 'roleGroupID')
            return self.__roleGroupings

    def GetLocationalRoles(self):
        return self.__locationalRoles

    def PayoutDividend(self, payShareholders, payoutAmount):
        return self.GetCorpRegistry().PayoutDividend(payShareholders, payoutAmount)

    def UpdateDivisionNames(self, divisions1, divisions2, divisions3, divisions4, divisions5, divisions6, divisions7, walletDivision1, walletDivision2, walletDivision3, walletDivision4, walletDivision5, walletDivision6, walletDivision7):
        res = self.GetCorpRegistry().UpdateDivisionNames(divisions1, divisions2, divisions3, divisions4, divisions5, divisions6, divisions7, walletDivision1, walletDivision2, walletDivision3, walletDivision4, walletDivision5, walletDivision6, walletDivision7)
        self.__hierarchicalRoles = None
        self.__roleGroupings = None
        self.__roleGroupingsForTitles = None
        return res

    def __ResignFromCEO(self, newCeoID = None):
        if newCeoID is None and eve.session.allianceid is not None and len(self.members.GetMembers()) < 2:
            raise UserError('CanNotDestroyCorpInAlliance')
        return self.GetCorpRegistry().ResignFromCEO(newCeoID)

    def ResignFromCEO(self):
        if not session.stationid2:
            eve.Message('CrpCanNotChangeCorpInSpace')
            return
        if not self.UserIsCEO():
            eve.Message('OnlyCEOCanResign')
            return
        memberCount = len(self.GetMembers())
        if memberCount <= 1:
            if eve.Message('CrpDestroyCorpWarning', {}, uiconst.YESNO, default=uiconst.ID_NO) != uiconst.ID_YES:
                return
        else:
            potentialCEOs = len(self.members.GetNumberOfPotentialCEOs())
            if potentialCEOs > 0:
                if eve.Message('AskResignAsCEO', {'memberCount': potentialCEOs}, uiconst.YESNO, default=uiconst.ID_NO) != uiconst.ID_YES:
                    return
            elif eve.Message('CrpDestroyNonEmptyCorpWarning', {}, uiconst.YESNO, default=uiconst.ID_NO) != uiconst.ID_YES:
                return
        res = sm.GetService('sessionMgr').PerformSessionChange('corp.resignceo', self.__ResignFromCEO)
        if res is None:
            return
        owners = []
        for charID in res:
            if charID not in owners:
                owners.append(charID)

        if len(owners):
            cfg.eveowners.Prime(owners)
        tmplist = []
        for charID in res:
            owner = cfg.eveowners.Get(charID)
            tmplist.append((owner.name, charID, owner.typeID))

        newCEO = uix.ListWnd(tmplist, 'character', localization.GetByLabel('UI/Corporations/BaseCorporationUI/SelectReplacementCEO'), localization.GetByLabel('UI/Corporations/BaseCorporationUI/SelectReplacementCEOText'), 1)
        if newCEO:
            newCeoID = newCEO[1]
            eve.session.ResetSessionChangeTimer('Retrying with selected alternate CEO')
            sm.GetService('sessionMgr').PerformSessionChange('corp.resignceo', self.__ResignFromCEO, newCeoID)

    def GetInfoWindowDataForChar(self, charID, acceptBlank = 0):
        data = self.GetCorpRegistry().GetInfoWindowDataForChar(charID)
        if not acceptBlank:
            if data.title1 is not None and len(data.title1) == 0:
                data.title1 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=1)
            if data.title2 is not None and len(data.title2) == 0:
                data.title2 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=2)
            if data.title3 is not None and len(data.title3) == 0:
                data.title3 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=3)
            if data.title4 is not None and len(data.title4) == 0:
                data.title4 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=4)
            if data.title5 is not None and len(data.title5) == 0:
                data.title5 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=5)
            if data.title6 is not None and len(data.title6) == 0:
                data.title6 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=6)
            if data.title7 is not None and len(data.title7) == 0:
                data.title7 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=7)
            if data.title8 is not None and len(data.title8) == 0:
                data.title8 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=8)
            if data.title9 is not None and len(data.title9) == 0:
                data.title9 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=9)
            if data.title10 is not None and len(data.title10) == 0:
                data.title10 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=10)
            if data.title11 is not None and len(data.title11) == 0:
                data.title11 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=11)
            if data.title12 is not None and len(data.title12) == 0:
                data.title12 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=12)
            if data.title13 is not None and len(data.title13) == 0:
                data.title13 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=13)
            if data.title14 is not None and len(data.title14) == 0:
                data.title14 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=14)
            if data.title15 is not None and len(data.title15) == 0:
                data.title15 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=15)
            if data.title16 is not None and len(data.title16) == 0:
                data.title16 = localization.GetByLabel('UI/Corporations/Common/TitleUntitled', index=16)
        return data

    def GetMemberTrackingInfo(self):
        if eve.session.corprole & const.corpRoleDirector:
            return self.GetCorpRegistry().GetMemberTrackingInfo()
        else:
            return self.GetCorpRegistry().GetMemberTrackingInfoSimple()

    def GetRentalDetailsPlayer(self):
        return self.GetCorpRegistry().GetRentalDetailsPlayer()

    def GetRentalDetailsCorp(self):
        return self.GetCorpRegistry().GetRentalDetailsCorp()

    def GetBulletins(self, isAlliance = False):
        if isAlliance:
            bulletins = sm.GetService('alliance').GetAllianceBulletins()
        else:
            bulletins = self.GetCorpBulletins()
        bulletinsList = []
        for dbrow in bulletins:
            b = util.KeyVal(dbrow)
            bulletinsList.append(b)

        bulletinsList.sort(lambda x, y: cmp(y.editDateTime, x.editDateTime))
        return bulletinsList

    def GetCorpBulletins(self):
        if self.bulletins is None or self.bulletinsTimestamp < blue.os.GetWallclockTime():
            self.bulletins = self.GetCorpRegistry().GetBulletins()
            self.bulletinsTimestamp = blue.os.GetWallclockTime() + 15 * MIN
        return self.bulletins

    def GetBulletinEntries(self, isAlliance = False):
        bulletins = self.GetBulletins(isAlliance)
        canEditCorp = const.corpRoleChatManager & session.corprole == const.corpRoleChatManager
        se = []
        for bulletin in bulletins:
            postedBy = localization.GetByLabel('UI/Corporations/BaseCorporationUI/BulletinPostedBy', charID=bulletin.editCharacterID, infoLinkData=('showinfo', cfg.eveowners.Get(bulletin.editCharacterID).typeID, bulletin.editCharacterID), postTime=bulletin.editDateTime)
            text = '<fontsize=18><b>%s</b></fontsize><br>%s' % (bulletin.title, bulletin.body)
            editLinks = ''
            if canEditCorp:
                editTag = '<a href="localsvc:service=corp&method=EditBulletin&id=%s">' % bulletin.bulletinID
                delTag = '<a href="localsvc:service=corp&method=DeleteBulletin&id=%s">' % bulletin.bulletinID
                editLinks = localization.GetByLabel('UI/Corporations/BaseCorporationUI/BulletinEditLinks', startEditTag=editTag, endEditTag='</a>', startDelTag=delTag, endDelTag='</a>')
            se.append(listentry.Get('BulletinEntry', {'text': text,
             'postedBy': postedBy + editLinks}))

        return se

    def GetBulletin(self, bulletinID):

        def FindBulletin(id, bulletins):
            bulletin = None
            for b in bulletins:
                if b.bulletinID == id:
                    bulletin = b
                    break

            return bulletin

        bulletin = None
        if bulletinID is not None:
            ownerID = session.corpid
            bulletins = self.GetBulletins()
            bulletin = FindBulletin(bulletinID, bulletins)
            if bulletin is None and session.allianceid:
                bulletins = self.GetBulletins(isAlliance=True)
                bulletin = FindBulletin(bulletinID, bulletins)
                ownerID = session.allianceid
            if bulletin is None:
                raise UserError('CorpBulletinNotFound')
        return bulletin

    def EditBulletin(self, id, isAlliance = False):
        if not const.corpRoleChatManager & eve.session.corprole == const.corpRoleChatManager:
            raise UserError('CrpAccessDenied', {'reason': localization.GetByLabel('UI/Corporations/BaseCorporationUI/DoNotHaveRole', roleName=localization.GetByMessageID(COMMUNICATIONS_OFFICER_ROLE_ID))})
        bulletin = self.GetBulletin(id)
        if bulletin and bulletin.ownerID == session.allianceid:
            isAlliance = True
        form.EditCorpBulletin.CloseIfOpen()
        form.EditCorpBulletin.Open(isAlliance=isAlliance, bulletin=bulletin)

    def DeleteBulletin(self, id):
        if not const.corpRoleChatManager & eve.session.corprole == const.corpRoleChatManager:
            raise UserError('CrpAccessDenied', {'reason': localization.GetByLabel('UI/Corporations/BaseCorporationUI/DoNotHaveRole', roleName=localization.GetByMessageID(COMMUNICATIONS_OFFICER_ROLE_ID))})
        if uicore.Message('ConfirmDeleteBulletin', {}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
            return
        bulletin = self.GetBulletin(id)
        if bulletin.ownerID == session.allianceid:
            sm.GetService('alliance').GetMoniker().DeleteBulletin(id)
        else:
            self.GetCorpRegistry().DeleteBulletin(id)
        self.RefreshBulletins()

    def AddBulletin(self, title, body, isAlliance):
        if len(self.GetBulletins(isAlliance)) >= MAX_NUM_BULLETINS:
            eve.Message('CorpTooManyBulletins')
            return
        if isAlliance:
            sm.GetService('alliance').GetMoniker().AddBulletin(title, body)
        else:
            self.GetCorpRegistry().AddBulletin(title, body)
        self.RefreshBulletins()

    def UpdateBulletin(self, bulletinID, title, body, isAlliance, editDateTime = None):
        try:
            if isAlliance:
                sm.GetService('alliance').GetMoniker().AddBulletin(title, body, bulletinID=bulletinID, editDateTime=editDateTime)
            else:
                self.GetCorpRegistry().AddBulletin(title, body, bulletinID=bulletinID, editDateTime=editDateTime)
        except UserError as e:
            eve.Message(e.msg, e.dict)

        self.RefreshBulletins()

    def RefreshBulletins(self):
        self.bulletins = None
        sm.GetService('alliance').bulletins = None
        sm.GetService('corpui').ResetWindow(1)

    def OnLockedItemChange(self, itemID, ownerID, locationID, change):
        self.itemLocking.OnLockedItemChange(itemID, ownerID, locationID, change)

    def GetLockedItemsByLocation(self, locationID):
        return self.itemLocking.GetLockedItemsByLocation(locationID)

    def GetLockedItemLocations(self):
        return self.itemLocking.GetLockedItemLocations()

    def IsItemLocked(self, item):
        return self.itemLocking.IsItemLocked(item)

    def IsItemIDLocked(self, itemID):
        return self.itemLocking.IsItemIDLocked(itemID)

    def GetRecruitmentAdTypes(self):
        if self.__recruitmentAdTypes is None:
            self._GetRecruitmentAdRegistryData()
        return self.__recruitmentAdTypes

    def GetRecruitmentAdGroups(self):
        if self.__recruitmentAdGroups is None:
            self._GetRecruitmentAdRegistryData()
        return self.__recruitmentAdGroups

    def _GetRecruitmentAdRegistryData(self):
        data = sm.RemoteSvc('corporationSvc').GetRecruitmentAdRegistryData()
        if boot.region == 'optic':
            for lst in [data.types, data.groups]:
                for idx, row in enumerate(lst):
                    if row.groupID == corputil.RECRUITMENT_GROUP_PRIMARY_LANGUAGE:
                        del lst[idx]

        for row in data.types:
            row.typeName = localization.GetByMessageID(row.typeNameID)
            row.description = localization.GetByMessageID(row.descriptionID)

        for row in data.groups:
            row.groupName = localization.GetByMessageID(row.groupNameID)
            row.description = localization.GetByMessageID(row.descriptionID)

        self.__recruitmentAdTypes = data.types
        self.__recruitmentAdGroups = data.groups

    def GetContactList(self):
        if util.IsNPC(session.corpid):
            return {}
        return self.GetCorpRegistry().GetCorporateContacts()

    def AddCorporateContact(self, contactID, relationshipID):
        self.GetCorpRegistry().AddCorporateContact(contactID, relationshipID)

    def EditCorporateContact(self, contactID, relationshipID):
        self.GetCorpRegistry().EditCorporateContact(contactID, relationshipID)

    def RemoveCorporateContacts(self, contactIDs):
        self.GetCorpRegistry().RemoveCorporateContacts(contactIDs)

    def EditContactsRelationshipID(self, contactIDs, relationshipID):
        self.GetCorpRegistry().EditContactsRelationshipID(contactIDs, relationshipID)

    def GetLabels(self):
        return self.GetCorpRegistry().GetLabels()

    def CreateLabel(self, name, color = 0):
        return self.GetCorpRegistry().CreateLabel(name, color)

    def DeleteLabel(self, labelID):
        self.GetCorpRegistry().DeleteLabel(labelID)

    def EditLabel(self, labelID, name = None, color = None):
        self.GetCorpRegistry().EditLabel(labelID, name, color)

    def AssignLabels(self, contactIDs, labelMask):
        self.GetCorpRegistry().AssignLabels(contactIDs, labelMask)

    def RemoveLabels(self, contactIDs, labelMask):
        self.GetCorpRegistry().RemoveLabels(contactIDs, labelMask)

    def GetAllyBaseCost(self):
        try:
            lastRefreshTime = self.allyBaseCost[1]
            if lastRefreshTime + 1 * const.MIN < blue.os.GetWallclockTime():
                self.RefreshAllyBaseCost()
        except AttributeError:
            self.RefreshAllyBaseCost()

        return self.allyBaseCost[0]

    def RefreshAllyBaseCost(self):
        self.allyBaseCost = (self.GetCorpRegistry().CharGetAllyBaseCost(), blue.os.GetWallclockTime())

    def LogCorpRecruitmentEvent(self, *args):
        if not sm.GetService('machoNet').GetGlobalConfig().get('disableCorpRecruitmentLogging', 0):
            uthread.new(self.DoLogCorpRecruitmentEvent, *args)

    def DoLogCorpRecruitmentEvent(self, *args):
        try:
            sm.ProxySvc('eventLog').LogClientEvent('corpRecruitment', *args)
        except UserError:
            pass

    def PrimeCorpRecruitmentData(self):
        if not hasattr(self, 'advertTypes'):
            self.advertTypes = self.GetRecruitmentAdTypes()
        if not hasattr(self, 'advertTypesByGroupID'):
            self.advertTypesByGroupID = self.advertTypes.Filter('groupID')
        if not hasattr(self, 'advertGroups'):
            self.advertGroups = self.GetRecruitmentAdGroups().Index('groupID')
        if not hasattr(self, 'advertTypesByTypeID'):
            self.advertTypesByTypeID = self.advertTypes.Filter('typeID')

    def GetCorpAdvertTypes(self):
        self.PrimeCorpRecruitmentData()
        return self.advertTypes

    def GetCorpAdvertTypesByGroupID(self, *args):
        self.PrimeCorpRecruitmentData()
        return self.advertTypesByGroupID

    def GetCorpAdvertGroups(self, *args):
        self.PrimeCorpRecruitmentData()
        return self.advertGroups

    def GetCorpAdvertTypesByTypeID(self, *args):
        self.PrimeCorpRecruitmentData()
        return self.advertTypesByTypeID

    def OpenCorpAdInNewWindow(self, corpID, adID, *args):
        corpAd = self.GetAdFromCorpAndAdID(corpID, adID)
        if not corpAd:
            return
        ads = [(None, corpAd)]
        dataList = self.GetRecruitementEntryDataList(ads, None, None, {})
        wnd = uicls.CorpRecruitmentAdStandaloneWindow.GetIfOpen(windowID='corAd_%s' % adID)
        if wnd and not wnd.destroyed:
            wnd.Maximize()
        else:
            uicls.CorpRecruitmentAdStandaloneWindow(windowID='corAd_%s' % adID, data=dataList[0])

    def GetRecruitementEntryDataList(self, ads, wantMask, wantLanguageMask, expandedAd, *args):
        dataList = []
        allIDsToPrime = set()
        warSvc = sm.GetService('war')
        corpWarsByCorpID = {}
        for grade, advert in ads:
            allIDsToPrime.add(advert.corporationID)
            regWars = warSvc.GetWars(advert.corporationID).values()
            if advert.allianceID:
                regWars.extend(warSvc.GetWars(advert.allianceID).values())
            facWars = []
            warFactionID = sm.StartService('facwar').GetCorporationWarFactionID(advert.corporationID)
            if warFactionID:
                facWars = sm.GetService('facwar').GetFactionWars(advert.corporationID).values()
            for wars in (regWars, facWars):
                for war in wars:
                    for warAtCorp in (war.declaredByID, war.againstID):
                        if advert.corporationID in corpWarsByCorpID:
                            if warAtCorp not in (session.corpid, session.allianceid, warFactionID):
                                corpWarsByCorpID[advert.corporationID].add(warAtCorp)
                        elif warAtCorp not in (session.corpid, session.allianceid, warFactionID):
                            corpWarsByCorpID[advert.corporationID] = set([warAtCorp])

                    allIDsToPrime.add(war.declaredByID)
                    allIDsToPrime.add(war.againstID)

            if advert.allianceID:
                allIDsToPrime.add(advert.allianceID)

        cfg.eveowners.Prime(allIDsToPrime)
        for grade, advert in ads:
            atWarWith = corpWarsByCorpID.get(advert.corporationID, set())
            data = self.GetRecruitmenEntryData(advert, wantMask, wantLanguageMask, expandedAd, atWarWith.copy(), grade)
            dataList.append(data)

        return dataList

    def GetRecruitmenEntryData(self, advert, wantMask, wantLanguageMask, expandedAd, atWarWith, grade, *args):
        data = util.KeyVal()
        data.advert = advert
        data.createDateTime = advert.createDateTime
        data.corporationID = advert.corporationID
        data.allianceID = advert.allianceID
        data.channelID = advert.channelID
        data.corpView = False
        data.grade = grade
        memberCount = sm.GetService('corp').GetCorporation(advert.corporationID).memberCount
        data.memberCount = memberCount
        data.searchMask = wantMask
        data.searchLangMask = wantLanguageMask
        data.expandedView = expandedAd.get(data.corpView, None) == advert.adID
        data.standaloneMode = False
        data.adTitle = advert.title
        data.timeZoneMask1 = advert.hourMask1
        data.timeZoneMask2 = advert.hourMask2
        data.warOpponents = atWarWith
        if data.expandedView:
            data.recruiters = self.GetRecruiters(advert.adID)
        return data
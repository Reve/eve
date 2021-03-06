#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/services/mail/notificationSvc.py
import service
import blue
import sys
import log
import const
import util
import copy
import notificationUtil
import form
import uiconst
import yaml
import localization

class notificationSvc(service.Service):
    __guid__ = 'svc.notificationSvc'
    __displayname__ = 'Notification service'
    __exportedcalls__ = {}
    __notifyevents__ = ['OnNotificationReceived', 'OnNotificationDeleted', 'OnNotificationUndeleted']
    __startupdependencies__ = ['settings']

    def __init__(self):
        service.Service.__init__(self)

    def Run(self, ms = None):
        self.state = service.SERVICE_RUNNING
        self.notificationMgr = sm.RemoteSvc('notificationMgr')
        self.notifications = {}
        self.unreadCount = {}
        self.unreadNotifications = None
        self.blinkTab = False
        self.blinkNeocom = False

    def ClearCache(self):
        self.notifications = {}
        self.unreadCount = {}
        self.unreadNotifications = None

    def GetNotificationsByGroupID(self, groupID):
        if groupID not in self.notifications:
            self.notifications[groupID] = []
            cache = self.notifications[groupID]
            newNotifications = self.notificationMgr.GetByGroupID(groupID)
            newSenders = []
            for newNotification in newNotifications:
                cache.append(util.KeyVal(notificationID=newNotification.notificationID, typeID=newNotification.typeID, senderID=newNotification.senderID, receiverID=newNotification.receiverID, processed=newNotification.processed, created=newNotification.created, data=newNotification.data, deleted=False))
                newSenders.append(newNotification.senderID)

            sm.GetService('mailSvc').PrimeOwners(newSenders)
        return self.notifications[groupID]

    def GetUnreadNotifications(self):
        self.LogInfo('Getting unread notifications')
        if self.unreadNotifications is None:
            unreadNotifications = []
            newNotifications = self.notificationMgr.GetUnprocessed()
            newSenders = []
            for newNotification in newNotifications:
                unreadNotifications.append(util.KeyVal(notificationID=newNotification.notificationID, typeID=newNotification.typeID, senderID=newNotification.senderID, receiverID=newNotification.receiverID, processed=newNotification.processed, created=newNotification.created, data=newNotification.data, deleted=False))
                newSenders.append(newNotification.senderID)
                groupID = notificationUtil.GetTypeGroup(newNotification.typeID)
                if groupID in self.unreadCount:
                    self.unreadCount[groupID] = self.unreadCount[groupID] + 1
                else:
                    self.unreadCount[groupID] = 1

            self.unreadNotifications = unreadNotifications
            sm.GetService('mailSvc').PrimeOwners(newSenders)
        return self.unreadNotifications

    def GetUnreadCount(self):
        if self.unreadNotifications is None:
            self.GetUnreadNotifications()
        return self.unreadCount

    def GetAllUnreadCount(self):
        unreadCounts = self.GetUnreadCount().copy()
        unreadGroupCounter = 0
        for counter in unreadCounts.itervalues():
            unreadGroupCounter += counter

        unreadCounts[const.notificationGroupUnread] = unreadGroupCounter
        return unreadCounts

    def CheckShouldStopBlinking(self, *args):
        allUnreadGroups = self.GetAllUnreadCount()
        allUnread = allUnreadGroups.get(const.notificationGroupUnread, 0)
        if allUnread == 0:
            self.StopNotificationBlinking()

    def StopNotificationBlinking(self, *args):
        self.SetBlinkTabState(False)
        sm.ScatterEvent('OnMailStartStopBlinkingTab', 'notifications', 0)
        self.SetBlinkNeocomState(False)
        if not settings.user.ui.Get('mail_blinkNecom', 1) or sm.GetService('mailSvc').ShouldNeocomBlink() == False:
            sm.GetService('neocom').BlinkOff('mail')

    def GetFormattedNotifications(self, groupID):
        notifications = self.GetNotificationsByGroupID(groupID)
        ret = self.FormatNotifications(notifications)
        return ret

    def GetFormattedUnreadNotifications(self):
        notifications = self.GetUnreadNotifications()
        ret = self.FormatNotifications(notifications)
        return ret

    def FormatNotifications(self, notifications):
        for notification in notifications:
            try:
                if isinstance(notification.data, basestring):
                    notification.data = yaml.load(notification.data, Loader=yaml.CSafeLoader)
            except Exception as e:
                self.LogWarn('Exception while un-yamling notification data', repr(notification.data), e)
                sys.exc_clear()

        self.PrimeNotificationLinkInfo(notifications)
        ret = []
        for notification in notifications:
            subject, body = notificationUtil.Format(notification)
            keyVal = notification.copy()
            keyVal.subject = subject
            keyVal.body = body
            ret.append(keyVal)

        return ret

    def PrimeNotificationLinkInfo(self, notifications):
        locationKeys = ('solarsystemid', 'stationid', 'clonestationid', 'corpstationid', 'moonid', 'locationid')
        ownerKeys = ('characterid', 'charid', 'corporationid', 'corpid', 'allianceid', 'deptorid', 'creditorid', 'aggressorid', 'aggressorcorpid', 'aggressorallianceid', 'factionid', 'podkillerid', 'againstid', 'declaredbyid', 'ownerid', 'oldownerid', 'newownerid', 'locationownerid', 'victimid')
        locationIDs = set()
        ownerIDs = set()
        for notification in notifications:
            data = notification.data
            if data is not None and isinstance(data, dict):
                for key, value in data.iteritems():
                    if isinstance(value, int):
                        if key.lower() in locationKeys:
                            locationIDs.add(value)
                        elif key.lower() in ownerKeys:
                            ownerIDs.add(value)

        cfg.evelocations.Prime(locationIDs)
        cfg.eveowners.Prime(ownerIDs)

    def MarkAllReadInGroup(self, groupID):
        notifications = self.GetNotificationsByGroupID(groupID)
        toMarkRead = []
        for read in notifications:
            for unread in self.unreadNotifications:
                if unread.notificationID == read.notificationID:
                    toMarkRead.append(read.notificationID)

        if len(toMarkRead) < 1:
            return
        if eve.Message('EvemailNotificationsMarkGroupRead', {}, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            self.notificationMgr.MarkGroupAsProcessed(groupID)
            self.UpdateCacheAfterMarkingRead(toMarkRead)
            sm.ScatterEvent('OnNotificationsRefresh')
        self.CheckShouldStopBlinking()

    def MarkAllRead(self):
        if not self.unreadNotifications:
            return
        self.notificationMgr.MarkAllAsProcessed()
        toMarkRead = []
        for notification in self.unreadNotifications:
            toMarkRead.append(notification.notificationID)

        self.UpdateCacheAfterMarkingRead(toMarkRead)
        sm.ScatterEvent('OnNotificationsRefresh')
        self.CheckShouldStopBlinking()

    def MarkAsRead(self, notificationIDs):
        if self.unreadNotifications is None:
            return
        notificationIDsToMarkAsRead = set()
        for notificationID in notificationIDs:
            for notification in self.unreadNotifications:
                if notificationID == notification.notificationID:
                    notificationIDsToMarkAsRead.add(notificationID)

        numToMark = len(notificationIDsToMarkAsRead)
        if numToMark < 1:
            return
        if numToMark > const.notificationsMaxUpdated:
            txt = localization.GetByLabel('UI/Mail/Notifications/TooManySelected', num=numToMark, max=const.notificationsMaxUpdated)
            raise UserError('CustomInfo', {'info': txt})
        notificationsList = list(notificationIDsToMarkAsRead)
        self.notificationMgr.MarkAsProcessed(notificationsList)
        self.UpdateCacheAfterMarkingRead(notificationsList)
        self.CheckShouldStopBlinking()

    def UpdateCacheAfterMarkingRead(self, notificationIDs):
        for readID in notificationIDs:
            wasUnread = False
            typeID = None
            for unread in self.unreadNotifications:
                if unread.notificationID == readID:
                    typeID = unread.typeID
                    self.unreadNotifications.remove(unread)
                    wasUnread = True
                    break

            if not wasUnread:
                continue
            groupID = notificationUtil.GetTypeGroup(typeID)
            if groupID in self.notifications:
                for grouped in self.notifications[groupID]:
                    if grouped.notificationID == readID:
                        grouped.processed = True
                        break

            if groupID in self.unreadCount:
                self.unreadCount[groupID] = self.unreadCount[groupID] - 1

    def DeleteAllFromGroup(self, groupID):
        notifications = self.GetNotificationsByGroupID(groupID)
        if len(notifications) < 1:
            return
        self.notificationMgr.DeleteGroupNotifications(groupID)
        deleted = []
        for notification in notifications:
            deleted.append(notification.notificationID)

        self.UpdateCacheAfterDeleting(deleted)
        sm.ScatterEvent('OnNotificationsRefresh')

    def DeleteAll(self):
        self.notificationMgr.DeleteAllNotifications()
        self.unreadNotifications = []
        self.unreadCount = {}
        if self.notifications is not None:
            for groupID in self.notifications.iterkeys():
                self.notifications[groupID] = []

        sm.ScatterEvent('OnNotificationsRefresh')

    def DeleteNotifications(self, notificationIDs):
        numToDelete = len(notificationIDs)
        if numToDelete < 1:
            return
        if numToDelete > const.notificationsMaxUpdated:
            txt = localization.GetByLabel('UI/Mail/Notifications/TooManySelected', num=numToDelete, max=const.notificationsMaxUpdated)
            raise UserError('CustomInfo', {'info': txt})
        self.notificationMgr.DeleteNotifications(notificationIDs)
        self.UpdateCacheAfterDeleting(notificationIDs)
        self.CheckShouldStopBlinking()

    def UpdateCacheAfterDeleting(self, notificationIDs):
        toclear = copy.copy(notificationIDs)
        if self.unreadNotifications is not None:
            for deletedID in notificationIDs:
                for unread in self.unreadNotifications:
                    if unread.notificationID == deletedID:
                        groupID = notificationUtil.GetTypeGroup(unread.typeID)
                        self.unreadNotifications.remove(unread)
                        if groupID in self.unreadCount:
                            self.unreadCount[groupID] = self.unreadCount[groupID] - 1
                        if groupID in self.notifications:
                            for grouped in self.notifications[groupID]:
                                if grouped.notificationID == deletedID:
                                    self.notifications[groupID].remove(grouped)
                                    break

                        toclear.remove(deletedID)
                        break

        if len(toclear) > 0:
            for groupID in self.notifications:
                for deletedID in copy.copy(toclear):
                    for grouped in self.notifications[groupID]:
                        if grouped.notificationID == deletedID:
                            self.notifications[groupID].remove(grouped)
                            toclear.remove(deletedID)
                            break

    def OnNotificationDeleted(self, notificationIDs):
        toclear = copy.copy(notificationIDs)
        if self.unreadNotifications is not None:
            for deletedID in notificationIDs:
                for unread in self.unreadNotifications:
                    if unread.notificationID == deletedID:
                        groupID = notificationUtil.GetTypeGroup(self.unreadNotifications[deletedID].typeID)
                        self.unreadNotifications.remove(unread)
                        if groupID in self.unreadCount:
                            self.unreadCount[groupID] = self.unreadCount[groupID] - 1
                        if groupID in self.notifications:
                            for grouped in self.notifications[groupID]:
                                if grouped.notificationID == deletedID:
                                    self.notifications[groupID].remove(grouped)
                                    break

                        toclear.remove(deletedID)
                        break

        if len(toclear) > 0:
            for groupID in self.notifications:
                for deletedID in copy.copy(toclear):
                    for grouped in self.notifications[groupID]:
                        if grouped.notificationID == deletedID:
                            self.notifications[groupID].remove(grouped)
                            toclear.remove(deletedID)
                            break

        sm.ScatterEvent('OnNotificationsRefresh')

    def OnNotificationUndeleted(self, notificationIDs):
        self.ClearCache()
        sm.ScatterEvent('OnNotificationsRefresh')

    def OnNotificationReceived(self, notificationID, typeID, senderID, created, data = {}):
        self.SetBlinkTabState(True)
        notification = util.KeyVal(notificationID=notificationID, typeID=typeID, senderID=senderID, receiverID=session.charid, processed=False, created=created, data=data, deleted=False)
        groupID = notificationUtil.GetTypeGroup(typeID)
        if groupID is None:
            log.LogException('No group for typeID = %s' % typeID)
        else:
            if groupID in self.notifications:
                self.notifications[groupID].insert(0, notification)
            if self.unreadNotifications is not None:
                if groupID in self.unreadCount:
                    self.unreadCount[groupID] = self.unreadCount[groupID] + 1
                else:
                    self.unreadCount[groupID] = 1
                self.unreadNotifications.insert(0, notification)
        self.ScatterNotificationEvent(notification)
        if settings.user.ui.Get('notification_showNotification', 1):
            self.GetNotificationNotification(notification)
        if settings.user.ui.Get('notification_blinkNecom', 1):
            sm.GetService('neocom').Blink('mail')

    def ScatterNotificationEvent(self, notification):
        sm.ScatterEvent('OnNewNotificationReceived')

    def GetNotificationNotification(self, notification):
        n = self.FormatNotifications([notification])
        if len(n) < 1:
            return
        first = n[0]
        header = localization.GetByLabel('UI/Mail/Notifications/NewNotification')
        senderName = cfg.eveowners.Get(first.senderID).ownerName
        text1 = '%s: %s' % (localization.GetByLabel('UI/Mail/From'), senderName)
        if len(first.subject) > 100:
            text2 = '%s...' % first.subject[:100]
        else:
            text2 = first.subject
        icon = sm.GetService('mailSvc').ShowMailNotification(header, text1, text2)
        icon.OnClick = (self.OnClickingPopup, icon, first)
        icon.GetMenu = self.NotificationMenu

    def OnClickingPopup(self, popup, first, *args):
        self.OpenNotificationReadingWnd(first)
        if popup and not popup.destroyed:
            popup.CloseNotification()

    def GetReadingText(self, senderID, subject, created, message):
        sender = cfg.eveowners.Get(senderID)
        senderTypeID = sender.typeID
        if senderTypeID is not None and senderTypeID > 0:
            senderText = '<a href="showinfo:%(senderType)s//%(senderID)s">%(senderName)s</a>' % {'senderType': senderTypeID,
             'senderID': senderID,
             'senderName': sender.name}
        else:
            senderText = sender.name
        date = util.FmtDate(created, 'ls')
        newmsgText = localization.GetByLabel('UI/Mail/NotificationText', subject=subject, sender=senderText, date=date, body=message)
        return newmsgText

    def OpenNotificationReadingWnd(self, info, *args):
        wndName = 'mail_readingWnd_%s' % info.notificationID
        wnd = form.MailReadingWnd.Open(windowID=wndName, mail=None, msgID=info.notificationID, txt='', toolbar=False, trashed=False, type=const.mailTypeNotifications)
        if not info.processed:
            self.MarkAsRead([info.notificationID])
            sm.ScatterEvent('OnNotificationReadOutside', info.notificationID)
        if wnd is not None:
            wnd.Maximize()
            blue.pyos.synchro.SleepWallclock(1)
            txt = sm.GetService('notificationSvc').GetReadingText(info.senderID, info.subject, info.created, info.body)
            wnd.SetText(txt)

    def NotificationMenu(self, *args):
        m = [('Disable Notification ', self.DisableNotification)]
        return m

    def DisableNotification(self, *args):
        settings.user.ui.Set('notification_showNotification', 0)

    def ShouldTabBlink(self, *args):
        return self.blinkTab

    def SetBlinkTabState(self, state = False):
        self.blinkTab = state

    def ShouldNeocomBlink(self, *args):
        return self.blinkNeocom

    def SetBlinkNeocomState(self, state = False):
        self.blinkNeocom = state
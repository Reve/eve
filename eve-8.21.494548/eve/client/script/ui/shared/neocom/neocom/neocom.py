#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/neocom/neocom/neocom.py
import uicls
import uiconst
import util
import uthread
import neocom
import base
import blue
import skillUtil
import service
import uiutil
import localization
import form
import trinity
import telemetry

class Neocom(uicls.Container):
    __guid__ = 'neocom.Neocom'
    __notifyevents__ = ['OnUIColorsChanged',
     'OnHeadNodeChanged',
     'OnSkillStarted',
     'OnSkillQueueRefreshed',
     'OnSkillPaused',
     'OnEveMenuOpened',
     'OnEveMenuClosed']
    default_name = 'Neocom'
    default_align = uiconst.TOLEFT
    default_state = uiconst.UI_NORMAL
    default_width = 40
    COLOR_CORNERFILL = (0, 0, 0, 0.5)
    NEOCOM_MINSIZE = 32
    NEOCOM_MAXSIZE = 64

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.updateClockThread = None
        self.autoHideActive = settings.char.ui.Get('neocomAutoHideActive', False)
        self.align = settings.char.ui.Get('neocomAlign', self.default_align)
        self.isHidden = False
        self.overflowButtons = []
        self.isResizingNeocom = False
        self.updateSkillThread = None
        self.width = settings.user.windows.Get('neocomWidth', self.default_width)
        self.resizeLineCont = uicls.Container(parent=self, name='resizeLineCont', align=uiconst.TOALL)
        self.mainCont = uicls.Container(parent=self, name='mainCont', align=uiconst.TOALL)
        self._ConstructBackground()
        self._ConstructBaseLayout()
        self._ConstructClock()
        self._ConstructCharCont()
        self.UpdateButtons()
        self.UpdateClock()
        if self.autoHideActive:
            self.HideNeocom()
        isElevated = eve.session.role & service.ROLEMASK_ELEVATEDPLAYER
        if isElevated and settings.public.ui.Get('Insider', True):
            uthread.new(sm.GetService('insider').Show, True, True)

    def _ConstructBackground(self):
        self.bgGradient = uicls.GradientSprite(bgParent=self, align=uiconst.TOALL)
        self._SetBgGradientColor()
        if self.align == uiconst.TOLEFT:
            align = uiconst.TORIGHT
        else:
            align = uiconst.TOLEFT
        self.resizeLine = uicls.Line(parent=self.resizeLineCont, color=(0, 0, 0, 0), align=align, weight=3, state=uiconst.UI_NORMAL)
        self.resizeLine.OnMouseDown = self.OnReisizeLineMouseDown
        self.resizeLine.OnMouseEnter = self.OnResizeLineMouseEnter
        self.SetResizeLineCursor()

    def SetResizeLineCursor(self):
        if self.IsSizeLocked():
            self.resizeLine.cursor = None
        else:
            self.resizeLine.cursor = uiconst.UICURSOR_LEFT_RIGHT_DRAG

    def OnReisizeLineMouseDown(self, *args):
        if not self.IsSizeLocked():
            uthread.new(self.OnResizerDrag)

    def OnResizeLineMouseEnter(self, *args):
        if self.isHidden:
            self.UnhideNeocom()

    def OnResizerDrag(self, *args):
        while uicore.uilib.leftbtn and not self.destroyed:
            self.isResizingNeocom = True
            if self.align == uiconst.TOLEFT:
                width = uicore.uilib.x
            elif self.align == uiconst.TORIGHT:
                width = uicore.desktop.width - uicore.uilib.x
            if width != self.width:
                self.width = max(self.NEOCOM_MINSIZE, min(width, self.NEOCOM_MAXSIZE))
                self._ConstructCharCont()
                settings.user.windows.Set('neocomWidth', self.width)
                sm.ScatterEvent('OnNeocomResized')
            blue.synchro.SleepWallclock(100)

        self.isResizingNeocom = False

    def _SetBgGradientColor(self):
        color = settings.char.windows.Get('wndColor', eve.themeColor)
        r, g, b, a = color
        self.bgGradient.SetGradient([(0.0, (r, g, b))], [(0.0, max(0.0, a - 0.3)), (1.0, a)])

    def _ConstructBaseLayout(self):
        self.charCont = uicls.ContainerAutoSize(parent=self.mainCont, name='charCont', align=uiconst.TOTOP)
        self.clockCont = neocom.WrapperButton(parent=self.mainCont, name='clockCont', align=uiconst.TOBOTTOM, height=20, cmdName='OpenCalendar')
        self.fixedButtonCont = uicls.ContainerAutoSize(parent=self.mainCont, name='fixedButtonCont', align=uiconst.TOBOTTOM)
        uicls.Fill(bgParent=self.fixedButtonCont, color=self.COLOR_CORNERFILL, blendMode=trinity.TR2_SBM_ADD)
        self.overflowBtn = neocom.OverflowButton(parent=self.mainCont, align=uiconst.TOBOTTOM, state=uiconst.UI_HIDDEN, height=20)
        self.buttonCont = uicls.Container(parent=self.mainCont, name='buttonCont', align=uiconst.TOALL)
        self.dropIndicatorLine = uicls.Line(parent=self.mainCont, name='dropIndicatorLine', align=uiconst.TOPLEFT, color=util.Color.GetGrayRGBA(0.7, 0.3), pos=(0, 0, 0, 1))

    def _ConstructCharCont(self):
        self.charCont.Flush()
        self.eveMenuBtn = neocom.ButtonEveMenu(parent=self.charCont, name='eveMenuBtn', align=uiconst.TOTOP, height=30, cmdName='OpenEveMenu', btnData=sm.GetService('neocom').eveMenuBtnData)
        self.charSheetBtn = neocom.WrapperButton(parent=self.charCont, name='charSheetBtn', align=uiconst.TOTOP, height=self.width, cmdName='OpenCharactersheet')
        self.skillTrainingCont = neocom.WrapperButton(parent=self.charCont, name='skillTrainingCont', align=uiconst.TOTOP, height=9, cmdName='OpenSkillQueueWindow')
        self.skillTrainingCont.GetHint = self._GetSkillTrainingContHint
        self.skillTrainingFill = uicls.Sprite(parent=uicls.Container(parent=self.skillTrainingCont, state=uiconst.UI_DISABLED), name='trainingProgressFill', align=uiconst.TOLEFT_PROP, texturePath='res:/UI/Texture/classes/Neocom/trainingGradient.png', padding=1)
        uicls.Frame(parent=self.skillTrainingCont, cornerSize=3, name='trainingProgressBG', align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/Neocom/trainingBG.png', color=(1.0, 1.0, 1.0, 1.0))
        if self.updateSkillThread:
            self.updateSkillThread.kill()
        self.updateSkillThread = uthread.new(self._UpdateSkillInfo)
        charPic = uicls.Sprite(parent=self.charSheetBtn, name='charPic', ignoreSize=True, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        sm.GetService('photo').GetPortrait(eve.session.charid, 256, charPic)

    def _GetSkillTrainingContHint(self, *args):
        hint = neocom.WrapperButton.GetHint(self.skillTrainingCont)
        skill = sm.GetService('skills').SkillInTraining()
        hint += '<br>'
        if skill is None or skill.skillTrainingEnd is None:
            hint += '<br>' + localization.GetByLabel('UI/Neocom/NoSkillHint')
        else:
            secUntilDone = max(0L, long(skill.skillTrainingEnd) - blue.os.GetTime())
            hint += localization.GetByLabel('UI/Neocom/SkillTrainingHint', skillName=skill.name, skillLevel=skill.skillLevel + 1, time=secUntilDone)
        return hint

    def _UpdateSkillInfo(self):
        while not self.destroyed:
            self._UpdateSkillBar()
            blue.pyos.synchro.Sleep(5000)

    def _UpdateSkillBar(self):
        skill = sm.StartService('skills').SkillInTraining()
        if not skill:
            trainingProgressRatio = 0.0
        else:
            currSkillPoints = sm.GetService('skillqueue').GetSkillPointsFromSkillObject(skill)
            skillPointsAtStartOfLevel = skillUtil.GetSPForLevelRaw(skill.skillTimeConstant, skill.skillLevel)
            trainingProgressRatio = (currSkillPoints - skillPointsAtStartOfLevel) / float(skill.spHi - skillPointsAtStartOfLevel)
        if trainingProgressRatio == 0.0:
            self.skillTrainingFill.Hide()
        else:
            self.skillTrainingFill.Show()
            self.skillTrainingFill.width = trainingProgressRatio

    def OnSkillStarted(self, typeID = None, level = None):
        self._UpdateSkillBar()

    def OnSkillQueueRefreshed(self):
        self._UpdateSkillBar()

    def OnSkillPaused(self, typeID):
        self._UpdateSkillBar()

    @telemetry.ZONE_METHOD
    def UpdateButtons(self):
        self.fixedButtonCont.Flush()
        if session.stationid is not None:
            for i, btnData in enumerate(sm.GetService('neocom').GetScopeSpecificButtonData().children):
                btnClass = neocom.GetBtnClassByBtnType(btnData.btnType)
                btnUI = btnClass(parent=self.fixedButtonCont, name=btnData.id, btnData=btnData, align=uiconst.TOPLEFT, btnNum=i, width=self.width, isDraggable=False)
                btnData.btnUI = btnUI

        self.buttonCont.Flush()
        isDraggable = not self.IsSizeLocked()
        for i, btnData in enumerate(sm.GetService('neocom').GetButtonData()):
            btnClass = neocom.GetBtnClassByBtnType(btnData.btnType)
            btnUI = btnClass(parent=self.buttonCont, name=btnData.id, btnData=btnData, align=uiconst.TOPLEFT, btnNum=i, width=self.width, isDraggable=isDraggable)
            btnData.btnUI = btnUI

        self.CheckOverflow()
        sm.GetService('neocom').OnNeocomButtonsRecreated()

    def CheckOverflow(self):
        self.overflowButtons = []
        w, h = self.buttonCont.GetAbsoluteSize()
        for btnUI in self.buttonCont.children:
            if btnUI.top + btnUI.height > h:
                btnUI.Hide()
                self.overflowButtons.append(btnUI.btnData)
            else:
                btnUI.Show()

        if self.overflowButtons:
            newState = uiconst.UI_NORMAL
        else:
            newState = uiconst.UI_HIDDEN
        if self.overflowBtn.state != newState:
            self.overflowBtn.state = newState
            self.CheckOverflow()

    def _ConstructClock(self):
        clockMain = uicls.Container(parent=self.clockCont, align=uiconst.TOALL)
        uicls.Fill(parent=self.clockCont, color=self.COLOR_CORNERFILL)
        self.clockLabel = uicls.Label(parent=clockMain, name='clockLabel', align=uiconst.CENTER, fontsize=11)

    def UpdateClock(self):
        if self.updateClockThread:
            self.updateClockThread.kill()
        self.updateClockThread = uthread.new(self._UpdateClock)

    def _UpdateClock(self):
        chinaOffset = 0
        if boot.region == 'optic':
            chinaOffset = 8 * const.HOUR
        while not self.destroyed:
            year, month, weekday, day, hour, minute, second, msec = blue.os.GetTimeParts(blue.os.GetTime() + chinaOffset)
            self.clockLabel.text = '<b>%2.2i:%2.2i' % (hour, minute)
            blue.synchro.SleepWallclock(5000)

    def GetMenu(self):
        return sm.GetService('neocom').GetMenu()

    def SetSizeLocked(self, isLocked):
        settings.char.ui.Set('neocomSizeLocked', isLocked)
        self.SetResizeLineCursor()
        for btn in self.buttonCont.children:
            btn.SetDraggable(not isLocked)

    def IsSizeLocked(self):
        return settings.char.ui.Get('neocomSizeLocked', False)

    def IsAutoHideActive(self):
        return settings.char.ui.Get('neocomAutoHideActive', False)

    def SetAutoHideOn(self):
        settings.char.ui.Set('neocomAutoHideActive', True)
        self.autoHideActive = True
        uthread.new(self.AutoHideThread)

    def SetAutoHideOff(self):
        settings.char.ui.Set('neocomAutoHideActive', False)
        self.autoHideActive = False
        self.UnhideNeocom()

    def SetAlignRight(self):
        settings.char.ui.Set('neocomAlign', uiconst.TORIGHT)
        self.align = uiconst.TORIGHT
        self.resizeLine.align = uiconst.TOLEFT
        self.overflowBtn.UpdateIconRotation()
        self.SetOrder(0)

    def SetAlignLeft(self):
        settings.char.ui.Set('neocomAlign', uiconst.TOLEFT)
        self.align = uiconst.TOLEFT
        self.resizeLine.align = uiconst.TORIGHT
        self.overflowBtn.UpdateIconRotation()
        self.SetOrder(0)

    def OnUIColorsChanged(self, *args):
        self._SetBgGradientColor()

    def OnDropData(self, source, dropData):
        if not sm.GetService('neocom').IsValidDropData(dropData):
            return
        sm.GetService('neocom').OnBtnDataDropped(dropData[0])

    def OnDragEnter(self, panelEntry, dropData):
        if not sm.GetService('neocom').IsValidDropData(dropData):
            return
        sm.GetService('neocom').OnButtonDragEnter(sm.GetService('neocom').btnData, dropData[0])

    def OnDragExit(self, *args):
        self.HideDropIndicatorLine()

    def OnHeadNodeChanged(self, id):
        if id == 'neocom':
            self.UpdateButtons()
            self.HideDropIndicatorLine()

    def _OnSizeChange_NoBlock(self, width, height):
        uthread.new(self.UpdateButtons)

    def HideNeocom(self):
        endVal = 3 - self.width
        uicore.animations.MorphScalar(self, 'left', self.left, endVal, duration=0.7)
        self.isHidden = True

    def UnhideNeocom(self, sleep = False):
        if not self.isHidden:
            return
        uicore.animations.MorphScalar(self, 'left', self.left, 0, duration=0.2, sleep=sleep)
        self.isHidden = False
        if self.autoHideActive:
            uthread.new(self.AutoHideThread)

    def AutoHideThread(self):
        mouseNotOverTime = blue.os.GetTime()
        while not self.destroyed:
            blue.pyos.synchro.Sleep(50)
            if not self or self.destroyed:
                return
            if not self.IsAutoHideActive():
                return
            mo = uicore.uilib.mouseOver
            if mo == self or uiutil.IsUnder(mo, self):
                mouseNotOverTime = blue.os.GetTime()
                continue
            if sm.GetService('neocom').IsSomePanelOpen() or self.isResizingNeocom:
                mouseNotOverTime = blue.os.GetTime()
                continue
            if uicore.layer.menu.children:
                mouseNotOverTime = blue.os.GetTime()
                continue
            if sm.GetService('neocom').IsDraggingButtons():
                mouseNotOverTime = blue.os.GetTime()
                continue
            if blue.os.GetTime() - mouseNotOverTime > SEC:
                self.HideNeocom()
                return

    def ShowDropIndicatorLine(self, index):
        l, t = self.buttonCont.GetAbsolutePosition()
        self.dropIndicatorLine.state = uiconst.UI_DISABLED
        self.dropIndicatorLine.top = t + index * self.width
        self.dropIndicatorLine.width = self.width

    def HideDropIndicatorLine(self):
        self.dropIndicatorLine.state = uiconst.UI_HIDDEN

    def OnEveMenuOpened(self):
        for btn in self.buttonCont.children:
            uicore.animations.FadeTo(btn, btn.opacity, 0.5, duration=0.3)
            blue.synchro.SleepWallclock(20)

    def OnEveMenuClosed(self):
        for btn in self.buttonCont.children:
            uicore.animations.FadeTo(btn, btn.opacity, 1.0, duration=0.3)
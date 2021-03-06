#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/ui/control/scrollarea.py
import util
import blue
import telemetry
import base
import uthread
import log
import fontConst
import uiconst
import uiutil
import uicls
import types
import trinity
import mathUtil
import copy
SCROLLDIRECTION_V = 1
SCROLLDIRECTION_H = 2
SCROLLBARSIZE = 8

class ScrollAreaCore(uicls.Container):
    __guid__ = 'uicls.ScrollAreaCore'
    default_name = 'scrollarea'
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.isTabStop = 1
        self.activeframe = None
        self.content = None
        self.underlayContainer = None
        self.clipper = uicls.Container(name='__clipper', align=uiconst.TOALL, parent=self, clipChildren=True, padding=1)
        self.clipper._OnSizeChange_NoBlock = self.OnClipperSizeChange
        self.Prepare_()

    def SetContent(self, content):
        self.content = content

    @telemetry.ZONE_METHOD
    def GetVerticalScrollProportion(self):
        clipperWidth, clipperHeight = self.clipper.GetAbsoluteSize()
        verticalScrollRange = max(0, self.content.height - clipperHeight)
        if verticalScrollRange and self.content.top:
            return max(0.0, min(1.0, float(-self.content.top) / verticalScrollRange))
        return 0.0

    def GetHorizontalScrollProportion(self):
        clipperWidth, clipperHeight = self.clipper.GetAbsoluteSize()
        horizontalScrollRange = max(0, self.content.width - clipperWidth)
        if horizontalScrollRange and self.content.left:
            return max(0.0, min(1.0, float(-self.content.left) / horizontalScrollRange))
        return 0.0

    @telemetry.ZONE_METHOD
    def UpdateScrollProportion(self):
        clipperWidth, clipperHeight = self.clipper.GetAbsoluteSize()
        if self.verticalScrollControl:
            verticalScrollRange = max(0, self.content.height - clipperHeight)
            if verticalScrollRange:
                self.verticalScrollControl.state = uiconst.UI_NORMAL
                self.verticalScrollControl.UpdateHandlePositionAndSize(self.content, self.clipper)
            else:
                self.verticalScrollControl.state = uiconst.UI_HIDDEN
        if self.horizontalScrollControl:
            horizontalScrollRange = max(0, self.content.width - clipperWidth - self.verticalScrollControl.displayWidth)
            if horizontalScrollRange:
                self.horizontalScrollControl.state = uiconst.UI_NORMAL
                self.horizontalScrollControl.UpdateHandlePositionAndSize(self.content, self.clipper)
            else:
                self.horizontalScrollControl.state = uiconst.UI_HIDDEN

    @telemetry.ZONE_METHOD
    def ScrollToProportion(self, proportion, direction):
        clipperWidth, clipperHeight = self.clipper.GetAbsoluteSize()
        if direction == SCROLLDIRECTION_V:
            verticalScrollRange = max(0, self.content.height - clipperHeight)
            if verticalScrollRange:
                self.content.top = -int(verticalScrollRange * proportion)
            else:
                self.content.top = 0
        else:
            horizontalScrollRange = max(0, self.content.width - clipperWidth)
            if horizontalScrollRange:
                self.content.left = -int(horizontalScrollRange * proportion)
            else:
                self.content.left = 0
        self.UpdateScrollProportion()

    @telemetry.ZONE_METHOD
    def OnClipperSizeChange(self, newWidth, newHeight, *args, **kw):
        if not self.content:
            return
        if self.content.width != newWidth:
            positionBeforeResize = self.GetVerticalScrollProportion()
            hPositionBeforeResize = self.GetHorizontalScrollProportion()
            if hasattr(self.content, 'SetWidth'):
                self.content.SetWidth(newWidth)
            self.ScrollToProportion(positionBeforeResize, SCROLLDIRECTION_V)
            self.ScrollToProportion(hPositionBeforeResize, SCROLLDIRECTION_H)
        else:
            if self.content.height <= newHeight:
                self.content.top = 0
            else:
                minContentTop = newHeight - self.content.height
                self.content.top = max(minContentTop, self.content.top)
            self.UpdateScrollProportion()

    @telemetry.ZONE_METHOD
    def OnSetFocus(self, *args):
        if self.activeframe:
            self.activeframe.state = uiconst.UI_DISABLED

    @telemetry.ZONE_METHOD
    def OnKillFocus(self, *args):
        if self.activeframe:
            self.activeframe.state = uiconst.UI_HIDDEN

    @telemetry.ZONE_METHOD
    def OnMouseWheel(self, *etc):
        shiftContentY = int(uicore.uilib.dz * 0.25)
        clipperWidth, clipperHeight = self.clipper.GetAbsoluteSize()
        self.content.top = min(0, max(clipperHeight - self.content.height, self.content.top + shiftContentY))
        self.UpdateScrollProportion()

    def Scroll(self, dz):
        step = 37
        shiftContentY = int(dz * step)
        self.content.top = min(0, max(self.clipper.displayHeight - self.content.height, self.content.top + shiftContentY))
        self.UpdateScrollProportion()

    def Prepare_(self):
        self.Prepare_Underlay_()
        self.Prepare_ScrollControls_()
        self.Prepare_ActiveFrame_()

    def Prepare_ActiveFrame_(self):
        self.activeframe = None

    def Prepare_Underlay_(self):
        self.underlay = uicls.Fill(name='__underlay', color=(0.0, 0.0, 0.0, 0.5), parent=self)

    def Prepare_ScrollControls_(self):
        self.verticalScrollControl = uicls.ScrollAreaControls(name='__verticalScrollControl', parent=self, align=uiconst.TORIGHT, width=SCROLLBARSIZE, state=uiconst.UI_HIDDEN, scroll=self, scrollDirection=SCROLLDIRECTION_V, idx=0)
        self.horizontalScrollControl = uicls.ScrollAreaControls(name='__horizontalScrollControl', parent=self, align=uiconst.TOBOTTOM, height=SCROLLBARSIZE, scroll=self, scrollDirection=SCROLLDIRECTION_H, padRight=SCROLLBARSIZE, state=uiconst.UI_HIDDEN, idx=0)


class ScrollAreaControlsCore(uicls.Container):
    __guid__ = 'uicls.ScrollAreaControlsCore'
    default_clipChildren = True

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.scrollhandle = None
        self.scrollDirection = attributes.scrollDirection
        self.Prepare_()

    @telemetry.ZONE_METHOD
    def UpdateHandlePositionAndSize(self, content, clipper):
        if self.scrollhandle:
            clipperWidth, clipperHeight = self.parent.clipper.GetAbsoluteSize()
            contentWidth = content.width
            contentHeight = content.height
            contentLeft = content.left
            contentTop = content.top
            if self.scrollDirection == SCROLLDIRECTION_V:
                verticalSizeProportion = float(clipperHeight) / contentHeight
                self.scrollhandle.height = max(12, int(verticalSizeProportion * clipperHeight))
                absW, absH = self.GetAbsoluteSize()
                scrollRangeInPixels = contentHeight - clipperHeight
                handleRangeInPixels = absH - self.scrollhandle.height
                verticalPosProportion = min(1.0, -contentTop / float(scrollRangeInPixels))
                self.scrollhandle.top = int(verticalPosProportion * handleRangeInPixels)
            else:
                horizontalSizeProportion = float(clipperWidth) / contentWidth
                self.scrollhandle.width = max(12, int(horizontalSizeProportion * clipperWidth))
                absW, absH = self.GetAbsoluteSize()
                scrollRangeInPixels = contentWidth - clipperWidth
                handleRangeInPixels = absW - self.scrollhandle.width
                if scrollRangeInPixels:
                    horizontalPosProportion = -contentLeft / float(scrollRangeInPixels)
                else:
                    horizontalPosProportion = 0.0
                self.scrollhandle.left = int(horizontalPosProportion * handleRangeInPixels)

    @telemetry.ZONE_METHOD
    def ScrollToProportion(self, proportion):
        self.parent.ScrollToProportion(proportion, self.scrollDirection)

    @telemetry.ZONE_METHOD
    def Prepare_(self):
        if self.scrollDirection == SCROLLDIRECTION_V:
            self.scrollhandle = uicls.ScrollAreaHandle(name='__scrollhandle', parent=self, align=uiconst.TOPLEFT, width=self.width, state=uiconst.UI_NORMAL, scrollDirection=self.scrollDirection)
            self.underlay = uicls.Fill(name='__underlay', color=(0.0, 0.0, 0.0, 0.5), parent=self, padLeft=1)
        else:
            self.scrollhandle = uicls.ScrollAreaHandle(name='__scrollhandle', parent=self, align=uiconst.TOPLEFT, pos=(0,
             0,
             2,
             self.height), state=uiconst.UI_NORMAL, scrollDirection=self.scrollDirection)
            self.underlay = uicls.Fill(name='__underlay', color=(0.0, 0.0, 0.0, 0.5), parent=self, padTop=1)

    def OnMouseDown(self, *args):
        l, t, w, h = self.GetAbsolute()
        if self.scrollDirection == SCROLLDIRECTION_V:
            localCursor = uicore.uilib.y - t
            proportion = float(localCursor) / h
        else:
            localCursor = uicore.uilib.x - l
            proportion = float(localCursor) / w
        proportion = min(1.0, max(0.0, proportion))
        self.parent.ScrollToProportion(proportion, self.scrollDirection)

    def OnMouseMove(self, *args):
        if uicore.uilib.GetMouseCapture() is self:
            self.OnMouseDown()


class ScrollAreaHandleCore(uicls.Container):
    __guid__ = 'uicls.ScrollAreaHandleCore'

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.scrollDirection = attributes.scrollDirection
        self.hilite = None
        self._dragging = False
        self.Prepare_()

    def Prepare_(self):
        if self.scrollDirection == SCROLLDIRECTION_V:
            padding = (2, 1, 1, 1)
        else:
            padding = (1, 2, 1, 1)
        uicls.Fill(name='baseFill', color=(1.0, 1.0, 1.0, 0.25), parent=self, padding=padding)
        self.Prepare_Hilite_()

    def Prepare_Hilite_(self):
        if self.scrollDirection == SCROLLDIRECTION_V:
            padding = (2, 1, 1, 1)
        else:
            padding = (1, 2, 1, 1)
        self.hilite = uicls.Fill(parent=self, color=(1.0, 1.0, 1.0, 0.5), padding=padding, state=uiconst.UI_HIDDEN)

    def OnMouseDown(self, btn, *args):
        if btn != uiconst.MOUSELEFT:
            return
        if self.scrollDirection == SCROLLDIRECTION_V:
            self.startdragdata = (uicore.uilib.y, self.top)
        else:
            self.startdragdata = (uicore.uilib.x, self.left)
        self._dragging = 1

    def OnMouseMove(self, *etc):
        if not self._dragging:
            return
        if not uicore.uilib.leftbtn:
            self._dragging = 0
            return
        scrollTo = 0.0
        parentWidth, parentHeight = self.parent.GetAbsoluteSize()
        if self.scrollDirection == SCROLLDIRECTION_V:
            cursorInitY, initTop = self.startdragdata
            scrollRangeInPixels = parentHeight - self.height
            self.top = max(0, min(scrollRangeInPixels, initTop - cursorInitY + uicore.uilib.y))
            if scrollRangeInPixels and self.top:
                scrollTo = self.top / float(scrollRangeInPixels)
        else:
            cursorInitX, initLeft = self.startdragdata
            scrollRangeInPixels = parentWidth - self.width
            self.left = max(0, min(scrollRangeInPixels, initLeft - cursorInitX + uicore.uilib.x))
            if scrollRangeInPixels and self.left:
                scrollTo = self.left / float(scrollRangeInPixels)
        self.parent.ScrollToProportion(scrollTo)

    def OnMouseUp(self, btn, *args):
        if btn == uiconst.MOUSELEFT:
            self._dragging = 0

    def OnMouseEnter(self, *args):
        if self.hilite:
            self.hilite.state = uiconst.UI_DISABLED

    def OnMouseExit(self, *args):
        if self.hilite:
            self.hilite.state = uiconst.UI_HIDDEN
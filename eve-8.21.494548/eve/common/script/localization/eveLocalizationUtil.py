#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/common/script/localization/eveLocalizationUtil.py
import blue
import time
import calendar
import localization
import localizationUtil
import localizationInternalUtil
import telemetry
import eveLocalization

@telemetry.ZONE_FUNCTION
def FormatDateTime(value, **kwargs):
    formatStringList = []
    if kwargs.get('dateFormat', 'short') in ('full', 'long', 'medium', 'short'):
        formatStringList.append('%Y.%m.%d')
    timeFormat = kwargs.get('timeFormat', 'short')
    if timeFormat in ('full', 'long', 'medium'):
        formatStringList.append('%H:%M:%S')
    elif timeFormat == 'short':
        formatStringList.append('%H:%M')
    formatString = ' '.join(formatStringList)
    if isinstance(value, long):
        value = value + eveLocalization.GetTimeDelta() * const.SEC
        year, month, weekday, day, hour, minute, second, msec = blue.os.GetTimeParts(value)
        day_of_year = 1
        is_daylight_savings = -1
        value = (year,
         month,
         day,
         hour,
         minute,
         second,
         weekday,
         day_of_year,
         is_daylight_savings)
    elif isinstance(value, (time.struct_time, tuple)):
        value = calendar.timegm(value)
        value = time.gmtime(value + eveLocalization.GetTimeDelta())
    elif isinstance(value, float):
        value = time.gmtime(value + eveLocalization.GetTimeDelta())
    else:
        localization.LogError('datetime only accepts blue time or Python time as values, but we received a ', type(value).__name__, '.')
        return None
    return localizationInternalUtil.PrepareLocalizationSafeString(time.strftime(formatString, value), 'time')


@telemetry.ZONE_FUNCTION
def FormatGenericList(iterable, languageID = None, useConjunction = False):
    languageID = localizationInternalUtil.StandardizeLanguageID(languageID) or localizationUtil.GetLanguageID()
    stringList = [ unicode(each) for each in iterable ]
    delimiter = localization.GetByLabel('UI/Common/Formatting/ListGenericDelimiter')
    if not useConjunction or len(stringList) < 2:
        listString = delimiter.join(stringList)
    elif len(stringList) == 2:
        listString = localization.GetByLabel('UI/Common/Formatting/SimpleGenericConjunction', A=stringList[0], B=stringList[1])
    else:
        listPart = delimiter.join(stringList[:-1])
        listString = localization.GetByLabel('UI/Common/Formatting/ListGenericConjunction', list=listPart, lastItem=stringList[-1])
    return localizationInternalUtil.PrepareLocalizationSafeString(listString, messageID='genericlist')


localizationUtil.FormatDateTime = FormatDateTime
localizationUtil.FormatGenericList = FormatGenericList
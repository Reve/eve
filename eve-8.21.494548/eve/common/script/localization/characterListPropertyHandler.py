#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/common/script/localization/characterListPropertyHandler.py
import localization
import log

class CharacterListPropertyHandler(localization.BasePropertyHandler):
    __guid__ = 'localization.CharacterListPropertyHandler'
    PROPERTIES = {localization.CODE_UNIVERSAL: ('quantity', 'genders')}
    GENDER_NORMALIZATION_MAPPING = {1: localization.GENDER_MALE,
     0: localization.GENDER_FEMALE}

    def _GetQuantity(self, wrappedCharacters, languageID, *args, **kwargs):
        return len(wrappedCharacters)

    def _GetGenders(self, wrappedCharacters, languageID, *args, **kwargs):
        totalCharacters = len(wrappedCharacters)
        numberOfMales = 0
        numberOfFemales = 0
        for wrappedCharacter in wrappedCharacters:
            try:
                eveGender = cfg.eveowners.Get(wrappedCharacter).gender
            except KeyError:
                log.LogException()
                eveGender = 0

            characterGender = self.GENDER_NORMALIZATION_MAPPING[eveGender]
            if characterGender == localization.GENDER_FEMALE:
                numberOfFemales += 1
            else:
                numberOfMales += 1
                break

        resultType = localization.GENDERS_UNDEFINED
        if totalCharacters == 1:
            resultType = localization.GENDERS_EXACTLY_ONE_FEMALE if numberOfFemales == 1 else localization.GENDERS_EXACTLY_ONE_MALE
        elif totalCharacters > 1:
            resultType = localization.GENDERS_AT_LEAST_ONE_MALE if numberOfMales >= 1 else localization.GENDERS_ALL_FEMALE
        return resultType
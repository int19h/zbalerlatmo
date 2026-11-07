# Zbalermorna Unicode Space

This is a **proposed** list of distinct non-ligatured glyphs and potential names and values - Unicode names were chosen based on the [CSUR guide for naming glyphs](http://www.evertype.com/standards/csur/naming.html) and [the proposal for Tengwar](http://std.dkuug.dk/JTC1/SC2/WG2/docs/n1641/n1641.htm), and the glyph names are based on [the Adobe glyph naming standards](http://blogs.adobe.com/typblography/files/typblography/typotechnica2007/Glyph%20names.pdf). The CSUR hasn't been updated in some time, but the [UCSUR](https://www.kreativekorp.com/ucsur/) is acting as a holding area until they can be added to the CSUR - this could be considered being sent there if this is finalised. The `0xED80-0xEDBF` range is currently unused at the time of writing this.


    |       | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | A | B | C | D | E | F |
    |-------|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
    | 0xED8 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
    | 0xED9 |  |  |  |  |  |  |  |  |  |  |  |  |   |   |   |   |
    | 0xEDA |  |  |  |  |  |  |  |  |  |  |  |  |   |   |   |   |
    | 0xEDB |  |  |  |  |  |  |  |  |  |  |   |   |   |   |   |   |


```
Code Point C Glyph Name          Unicode Name
--------------------------------------------------------
U+ED89      denpabu             ZBALERMORNA SYMBOL FOR DENPA BU
U+ED8A      yhy                 ZBALERMORNA SYMBOL FOR YHY
U+ED8B      cnimahobu           ZBALERMORNA SYMBOL FOR CNIMAHO BU 

U+ED80      py                  ZBALERMORNA LETTER PY
U+ED81      ty                  ZBALERMORNA LETTER TY
U+ED82      ky                  ZBALERMORNA LETTER KY
U+ED83      fy                  ZBALERMORNA LETTER FY
U+ED84      ly                  ZBALERMORNA LETTER LY
U+ED85      sy                  ZBALERMORNA LETTER SY
U+ED86      cy                  ZBALERMORNA LETTER CY
U+ED87      my                  ZBALERMORNA LETTER MY
U+ED88      xy                  ZBALERMORNA LETTER XY
U+ED90      by                  ZBALERMORNA LETTER BY
U+ED91      dy                  ZBALERMORNA LETTER DY
U+ED92      gy                  ZBALERMORNA LETTER GY
U+ED93      vy                  ZBALERMORNA LETTER VY
U+ED94      ry                  ZBALERMORNA LETTER RY
U+ED95      zy                  ZBALERMORNA LETTER ZY
U+ED96      jy                  ZBALERMORNA LETTER JY
U+ED97      ny                  ZBALERMORNA LETTER NY
U+EDAA      iy                  ZBALERMORNA LETTER SEMIVOWEL IY
U+EDAB      uy                  ZBALERMORNA LETTER SEMIVOWEL UY

U+EDA0      abu                 ZBALERMORNA VOWEL SIGN ABU
U+EDA1      ebu                 ZBALERMORNA VOWEL SIGN EBU
U+EDA2      ibu                 ZBALERMORNA VOWEL SIGN IBU
U+EDA3      obu                 ZBALERMORNA VOWEL SIGN OBU
U+EDA4      ubu                 ZBALERMORNA VOWEL SIGN UBU
U+EDA5      ybu                 ZBALERMORNA VOWEL SIGN YBU
U+EDA6      aibu                ZBALERMORNA VOWEL SIGN AIBU
U+EDA7      eibu                ZBALERMORNA VOWEL SIGN EIBU
U+EDA8      oibu                ZBALERMORNA VOWEL SIGN OIBU
U+EDA9      aubu                ZBALERMORNA VOWEL SIGN AUBU

U+EDB0      seplimeabu          ZBALERMORNA LETTER FULL ABU
U+EDB1      seplimeebu          ZBALERMORNA LETTER FULL EBU
U+EDB2      seplimeibu          ZBALERMORNA LETTER FULL IBU
U+EDB3      seplimeobu          ZBALERMORNA LETTER FULL OBU
U+EDB4      seplimeubu          ZBALERMORNA LETTER FULL UBU
U+EDB5      seplimeybu          ZBALERMORNA LETTER FULL YBU
U+EDB6      seplimeaibu         ZBALERMORNA LETTER FULL AIBU
U+EDB7      seplimeeibu         ZBALERMORNA LETTER FULL EIBU
U+EDB8      seplimeoibu         ZBALERMORNA LETTER FULL OIBU
U+EDB9      seplimeaubu         ZBALERMORNA LETTER FULL AUBU

U+ED9A      slakabu             ZBALERMORNA SYMBOL FOR SLAKA BU
U+ED8C      patonga             ZBALERMORNA COMBINING PA TONGA
U+ED8C      retonga             ZBALERMORNA COMBINING RE TONGA
U+ED8D      citonga             ZBALERMORNA COMBINING CI TONGA
U+ED8E      votonga             ZBALERMORNA COMBINING VO TONGA
U+ED98      bahebu              ZBALERMORNA COMBINING BAHEBU
U+ED9B      tcenabu             ZBALERMORNA COMBINING TCENA BU
U+ED99      smajibu             ZBALERMORNA SYMBOL FOR SMAJI BU
```

Ligatures would then take the format `ty_abu`, `bahebu_bahebu`, `denpabu_yhy`, etc and would not be a part of the unicode spec, just as the other ligatures have been removed. It should be noted that in the current configuration and IME implementation, none of the diphthong code points are being used, and the {cnima'o bu} is only set up to display directly for reference - the ligatures aren't configured to combine with it - it may be worth it to consider removing the dipthongs to reduce the size of the space.

Additional glyphs would be the second and third ba'ebu, three positional smaji bu (init, medi, fina), vowel + yhy ligatures (10), and vowel.dot alternatives for self-dotting (10). With mark-base positional lookups, this is all that's needed to completely render ZLM.

Other glyphs like the question mark, exclamation mark, brakets, parenthesises, and braces may add to the font as well, for style.
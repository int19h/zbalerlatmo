log      = console.log.bind console
consonants = <[ ny dy ty zy sy gy jy xy iy ry my by py vy fy ky cy yhy uy ly denpabu denpabu.cas ]>
vowels = <[ abu ebu ibu obu ubu ybu aibu eibu oibu aubu ]>

log """
@consonant = [ py ty ky fy ly sy cy my xy \\by dy gy vy ry zy jy ny yhy iy uy ];
@singlevowel = [ abu ebu ibu obu ubu ybu ];
@vowel = [ @singlevowel aibu eibu oibu aubu ];
@anything = [ @consonant @vowel ];
@fullvowel = [ seplimeabu seplimeebu seplimeibu seplimeobu seplimeubu seplimeybu seplimeaibu seplimeeibu seplimeoibu seplimeaubu ];

languagesystem DFLT dflt;
languagesystem latn dflt;

lookup zlmSelfDottingCAS {
  lookupflag 0;
  ignore sub denpabu @vowel' yhy;
  ignore sub denpabu.cas @vowel' yhy;
  ignore sub @consonant @vowel' yhy;
  sub abu' yhy by denpabu.cas_abu;
  sub ebu' yhy by denpabu.cas_ebu;
  sub ibu' yhy by denpabu.cas_ibu;
  sub obu' yhy by denpabu.cas_obu;
  sub ubu' yhy by denpabu.cas_ubu;
  sub ybu' yhy by denpabu.cas_ybu;
  sub aibu' yhy by denpabu.cas_aibu;
  sub eibu' yhy by denpabu.cas_eibu;
  sub oibu' yhy by denpabu.cas_oibu;
  sub aubu' yhy by denpabu.cas_aubu;
} zlmSelfDottingCAS;

lookup zlmSelfDottingVowels {
  lookupflag 0;
  ignore sub @anything @vowel';
  ignore sub slakabu @vowel';
  ignore sub @vowel' slakabu;
  ignore sub denpabu @vowel';
  ignore sub denpabu.cas @vowel';
  sub abu' by denpabu_abu;
  sub ebu' by denpabu_ebu;
  sub ibu' by denpabu_ibu;
  sub obu' by denpabu_obu;
  sub ubu' by denpabu_ubu;
  sub ybu' by denpabu_ybu;
  sub aibu' by denpabu_aibu;
  sub eibu' by denpabu_eibu;
  sub oibu' by denpabu_oibu;
  sub aubu' by denpabu_aubu;
} zlmSelfDottingVowels;

"""

for c in consonants
  log "lookup mtb_ligatures_#c {"
  log "  lookupflag 0;"
  for v in vowels
    if (c == "by")
      log "  sub \\#c #v by #{c}_#{v};"
    else
      log "  sub #c #v by #{c}_#{v};"
  log "} mtb_ligatures_#c;"
  log ""
log "feature liga {"
log "  script DFLT;"
log "    language dflt;"
log "    lookup zlmSelfDottingCAS;"
log "    lookup zlmSelfDottingVowels;"
for c in consonants
  log "    lookup mtb_ligatures_#c;"
log "  script latn;"
log "    language dflt;"
log "    lookup zlmSelfDottingCAS;"
log "    lookup zlmSelfDottingVowels;"
for c in consonants
  log "    lookup mtb_ligatures_#c;"
log "} liga;"

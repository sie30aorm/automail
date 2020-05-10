import sys
import pandas as pd
import xml.etree.ElementTree as ET
import datetime
import re
import nltk
import json
from IPython.display import display, HTML
from pprint import pprint


# Acknoledgements:
# DNI/NIF/NIE validation from https://gist.github.com/afgomez/5691823
class RulesEngine:
    
    # ------------------------------------------------------
    def __init__(self, name='default', ruleset = [], ruleset_name = '', similar_distance=0, flag_conda=False ):
        self.my_flag_debug = False
        self.my_flag_conda = flag_conda
        self.my_ruleset_name = ruleset_name
        self.my_ruleset = ruleset
        self.my_name = name
        self.my_similar_distance = similar_distance
        # Dataframe to be evaluated
        self.my_df_name = ''
        self.my_df = None
        
        # Regular expressions to be used
        self.REGEXP_CASE = re.compile("\#?cas[oe][ \t]*[0-9]+")
        self.REGEXP_MOBILE_NUM = re.compile("[67](\d{8})")
        self.REGEXP_FIXED_NUM = re.compile("[1234589](\d{8})")
        self.REGEXP_DNI = re.compile("(\d{8})([A-Z])")
        self.REGEXP_NIF = re.compile("([ABCDEFGHJKLMNPQRSUVW])(\d{7})([0-9A-J])")
        self.REGEXP_NIE = re.compile("[XYZ]\d{7,8}[A-Z]")


    # ------------------------------------------------------
    def _debug_(self):
        self._log('   name             ={}'.format(self.my_name))
        self._log('   similar_distance ={}'.format(self.my_similar_distance))
        self._log('   flag_debug       ={}'.format(self.my_flag_debug))
        self._log('   dataframe_name   ={}'.format(self.my_df_name))
        self._log('   dataframe_cols   ={}'.format('' if self.my_df is None else self.my_df.columns))
        self._log('   ruleset_name     ={}'.format(self.my_ruleset_name))
        self._log('   ruleset          ={}'.format(self.my_ruleset))

    # ------------------------------------------------------
    def _log( self, txt ):
        if self.my_flag_conda:
            display(HTML( txt ))
        else:
            print( txt )
         
    # ------------------------------------------------------
    def _debug( self, txt ):
        if self.my_flag_debug:
            if self.my_flag_conda:
                display(HTML( txt ))
            else:
                print( txt )

    # ------------------------------------------------------
    def set_ruleset( self, ruleset, ruleset_name='none' ):
        self.my_ruleset = ruleset
        self.my_ruleset_name = ruleset_name

    # -----------------------------------------------------------------------------
    # Set dataframe
    # -----------------------------------------------------------------------------
    def set_dataframe( self, df, name='(unknown)' ):
        self.my_df      = df
        self.my_df_name = name
                
    # ------------------------------------------------------
    def set_similar_distance( self, similar_distance=0 ):
        self.my_similar_distance = similar_distance

        
    # ------------------------------------------------------
    def ruleset_dump( self ):
        pprint(self.my_ruleset)

    # ------------------------------------------------------
    def ruleset_load( self, filename ):
        try:
            with open(filename) as f:
                data = json.load(f)
                self.set_ruleset( data )
        except Exception,e:
            print("ERROR: while loading file "+filename )
            print("EXCEPCION: "+str(e))
            traceback.print_exc()
                    
    # ------------------------------------------------------
    def match( self, txt, matches, contains=True ):
        txt2  = str(txt).lower()
        # lowMatches = str(matches).lower()
        # Txt contains at least one the expressions
        if contains:
            for k in matches:
                if str(k).lower() in txt2:
                    self._debug("match {} '{}' <-> '{}'".format(contains,txt2,k))
                    return True
        # Txt equals one of the expression
        else:
            for k in matches:
                if txt2 == str(k).lower():
                    return True
        return False

    # ------------------------------------------------------
    def match_aprox( self, txt, matches ):
        for word in str(txt).split():
            for k in matches:
                curr_dist = nltk.edit_distance(word.lower(), k.lower())
                #if flag_debug:
                #    display(HTML("--> Distance from '{}' to '{}' = {}".format(word, k, curr_dist)))
                if curr_dist<=self.my_similar_distance:
                    if flag_debug:
                        print( "*** {} aprox. matches {}".format(txt,k))
                        # display(HTML("*** {} aprox. matches {}".format(txt,k)))
                    return True
        return False

    # ------------------------------------------------------
    def search_mobile_number( self, dat ):
        m = self.REGEXP_MOBILE_NUM.search(str(dat).lower())
        return '' if m is None else m.group(0)

    # ------------------------------------------------------
    def search_fixed_number( self, dat ):
        m = self.REGEXP_FIXED_NUM.search(str(dat).lower())
        return '' if m is None else m.group(0)
 
    # ------------------------------------------------------
    def search_cifnifnie( self, dat ):
        m = self.REGEXP_DNI.search(str(dat).upper())
        if m is not None:
            return m.group(0)
        
        m = self.REGEXP_NIF.search(str(dat).upper())
        if m is not None:
            return m.group(0)
        
        m = self.REGEXP_NIE.search(str(dat).upper())
        if m is not None:
            return m.group(0)
        
        return ''

    # ------------------------------------------------------
    def search_case_ref( self, dat ):
        m = self.REGEXP_CASE.search(str(dat).lower())
        if m is not None:
            out = m.group(0).replace(' ','')
            if not out.startswith('#'):
                out = '#'+out
            out = '#caso' + out[5:].zfill(8)
            return out
        return ''

    # --- RULE CONDITION --------------------------------------------
    def is_empty( self, idx, value, ifCond, theCONTEXT, VAL_TRUE, VAL_FALSE ):
        cond = VAL_FALSE
        if pd.isnull(value) or value is None or len(str(value))==0:
            cond = VAL_TRUE
        return cond

    # --- RULE CONDITION --------------------------------------------
    def contains_aprox( self, idx, value, ifCond, theCONTEXT, VAL_TRUE, VAL_FALSE ):
        if pd.isnull(value):
            return VAL_FALSE
        
        cond = VAL_FALSE
        evaluation  = ifCond['MATCH_VALUES']
        if self.match_aprox( value, evaluation ):
            cond = VAL_TRUE
        return cond
                                
    # --- RULE CONDITION --------------------------------------------
    def contains( self, idx, value, ifCond, theCONTEXT, VAL_TRUE, VAL_FALSE ):
        if pd.isnull(value):
            return VAL_FALSE
        
        cond = VAL_FALSE
        evaluation  = ifCond['MATCH_VALUES']
        if self.match( value, evaluation ):
             cond = VAL_TRUE
        return cond

    # --- RULE CONDITION --------------------------------------------
    def equals( self, idx, value, ifCond, theCONTEXT, VAL_TRUE, VAL_FALSE ):
        if pd.isnull(value):
            return VAL_FALSE

        cond = VAL_FALSE
        evaluation  = ifCond['MATCH_VALUES']
        if self.match( value, evaluation, contains=False ):
            cond = VAL_TRUE
        return cond

    # --- RULE CONDITION --------------------------------------------
    def match_regexp( self, idx, value, ifCond, theCONTEXT, VAL_TRUE, VAL_FALSE ):
        if pd.isnull( value ) or len(value)==0:
            return VAL_FALSE
        
        cond = VAL_FALSE
        evaluation  = ifCond['MATCH_VALUES']
        for expr in evaluation:
            match = re.search(expr, value)
            if match:
                if "AS" in ifCond:
                    theCONTEXT[ifCond['AS']] = match.group()
                cond = VAL_TRUE
                break
        return cond

    # --- RULE CONDITION --------------------------------------------
    def contains_case_ref( self, idx, value, ifCond, theCONTEXT, VAL_TRUE, VAL_FALSE ):
        if pd.isnull(value) or len(str(value))==0:
            return VAL_FALSE
        
        cond = VAL_FALSE
        txt = self.search_case_ref( value );
        if 'AS' in ifCond:
            theCONTEXT[ifCond['AS']] = txt

        if len(txt)>0:
            cond = VAL_TRUE
        return cond

    # --- RULE CONDITION --------------------------------------------
    def contains_mobile_num( self, idx, value, ifCond, theCONTEXT, VAL_TRUE, VAL_FALSE ):
        if pd.isnull(value) or len(str(value))==0:
            return VAL_FALSE
        
        txt = self.search_mobile_num( field_value );
        if len(txt)>0:
            cond = VAL_TRUE
        return cond

    # --- RULE CONDITION --------------------------------------------
    def contains_fixed_num( self, idx, value, ifCond, theCONTEXT, VAL_TRUE, VAL_FALSE ):
        if pd.isnull(value) or len(str(value))==0:
            return VAL_FALSE
        
        txt = self.search_fixed_num( value );
        if len(txt)>0:
            cond = VAL_TRUE
        return cond
            
    # --- RULE CONDITION --------------------------------------------
    def contains_nifcifnie( self, idx, value, ifCond, theCONTEXT, VAL_TRUE, VAL_FALSE ):
        if pd.isnull(value) or len(str(value))==0:
            return VAL_FALSE
        
        txt = self.search_cifnifnie( value );
        if len(txt)>0:
            cond = VAL_TRUE
        return cond

    # ------------------------------------------------------
    # CALL CONDITION METHOD
    # ------------------------------------------------------
    def evalCondition( self, idx, ifCond, theCONTEXT ):
        condition   = ifCond['COND']
        if '~' in condition:
            VAL_TRUE = False
            VAL_FALSE= True
            condition = condition.split("~")[1]
        else:
            VAL_TRUE = True
            VAL_FALSE= False
        f = getattr(self, condition, None)
        
        if callable(f):
            field_name = ifCond['FIELD']
            if not field_name in self.my_df.columns:
                self._debug( "evalCondition({}) - condition {} - field {}: returns FALSE".format(idx,condition,"NOT STATED"))
                return VAL_FALSE

            field_value = self.my_df.get_value(idx,field_name)
            self._debug( "evalCondition({}) - condition {} - field({})={}: calling...".format(idx,condition,field_name,field_value))
            out = f( self, field_value, ifCond, theCONTEXT, VAL_TRUE, VAL_FALSE )
            return out
        else:
            self._debug( "evalCondition({}) - condition {} NOT FOUND OR NOT CALLABLE".format(idx,condition))
            return VAL_FALSE

    # ------------------------------------------------------
    # LEFT SIDE EVALUATION
    # ------------------------------------------------------
    def eval_left_side( self, idx, theCONTEXT, theIF ):
        rule_match = False

        for ifCond in theIF:
            rule_match = self.evalCondition( idx, ifCond, theCONTEXT )
            self._debug( "eval_left_side({}) - condition {} - match = {}".format(idx,ifCond['COND'],rule_match))
            if( rule_match == False ):
                break

        return rule_match

    # ------------------------------------------------------
    # RIGHT SIDE EVALUATION
    # ------------------------------------------------------
    def eval_right_side( self, idx, theCONTEXT, theTHEN ):
            for action in theTHEN:
                if action['SET_VALUE']:
                    val = action['SET_VALUE']
                    if val in theCONTEXT:
                        val = theCONTEXT[val]
                    self.my_df.set_value(idx,action['FIELD'],val)

    # -----------------------------------------------------------------------------
    # evaluate a single rule on the preloaded dataframe. If no row-index is set, use whole dataframe
    # -----------------------------------------------------------------------------
    def evalRule( self, i, evalContext, rule ):
        #if flag_debug:
        #    display(HTML( "Checking rule: "+rule['RULE']))
        num_matches = 0
        evalContext = {}
        if rule['RULE']:
            evalContext['@RULE']=rule['RULE']
        if i==None:
            for i, row in self.my_df.iterrows():
                rule_match = self.eval_left_side(i, evalContext, rule['IF'] )
                if rule_match:
                    self._debug( "--> MATCH OK --> Go to the right side")
                    self.eval_right_side(i, rule['THEN'] )
                    num_matches += 1
        else:
            rule_match = self.eval_left_side(i, evalContext, rule['IF'] )
            if rule_match:
                self.eval_right_side(i, evalContext, rule['THEN'] )
                num_matches += 1
        return num_matches
        
    # -----------------------------------------------------------------------------
    # evaluate rulesets over dataframe
    # -----------------------------------------------------------------------------
    def evaluate( self, df=None, df_name='' ):
        if df is not None:
            self.set_dataframe( df, df_name )

        # for i in df.head().index:
        for i, row in self.my_df.iterrows():
            # for i in self.my_df.index:
            for ruleset in self.my_ruleset['ruleset']:
                #if flag_debug:
                #display(HTML( "Checking ruleset: "+ruleset['RULESET']))

                # Global RULESETs EVALUATION
                # 1: Eval if ruleset has global ifs
                rule_match = True
                evalContext = {}
                if 'GLOBAL-IF' in ruleset:
                    rule_match = self.eval_left_side(i, evalContext, ruleset['GLOBAL-IF'] )
                    # display(HTML("RULESET_IF returns {}".format(rule_match)))
                    if rule_match:
                        self.eval_right_side(i, evalContext, ruleset['GLOBAL-THEN'] )

                # Specific RULEs EVALUATION 
                # 2: If passed global ifs, eval rules inside the ruleset
                if rule_match:
                    if 'RULES' in ruleset:
                        for rule in ruleset['RULES']:
                            #print("EVAL RULE {}".format(rule) )
                            self.evalRule( i, evalContext, rule )

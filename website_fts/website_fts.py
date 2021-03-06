# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp import http
from openerp.http import request
from openerp.exceptions import Warning
from datetime import datetime, timedelta
import operator
import sys, traceback
import string

#from openerp.addons.website_fts.html2text import html2text
import re
from collections import Counter

import logging
_logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
except:
    _logger.info('website_fts requires bs4.')

# https://www.compose.com/articles/indexing-for-full-text-search-in-postgresql/

# https://github.com/ekorn/Keywords/blob/master/stopwords/swedish-stopwords.txt
STOP_WORDS = ['aderton','adertonde','adjö','aldrig','alla','allas','allt','alltid','alltså','än','andra','andras','annan','annat','ännu','artonde','artonn','åtminstone','att','åtta','åttio','åttionde','åttonde','av','även','båda','bådas','bakom','bara','bäst','bättre','behöva','behövas','behövde','behövt','beslut','beslutat','beslutit','bland','blev','bli','blir','blivit','bort','borta','bra','då','dag','dagar','dagarna','dagen','där','därför','de','del','delen','dem','den','deras','dess','det','detta','dig','din','dina','dit','ditt','dock','du','efter','eftersom','elfte','eller','elva','en','enkel','enkelt','enkla','enligt','er','era','ert','ett','ettusen','få','fanns','får','fått','fem','femte','femtio','femtionde','femton','femtonde','fick','fin','finnas','finns','fjärde','fjorton','fjortonde','fler','flera','flesta','följande','för','före','förlåt','förra','första','fram','framför','från','fyra','fyrtio','fyrtionde','gå','gälla','gäller','gällt','går','gärna','gått','genast','genom','gick','gjorde','gjort','god','goda','godare','godast','gör','göra','gott','ha','hade','haft','han','hans','har','här','heller','hellre','helst','helt','henne','hennes','hit','hög','höger','högre','högst','hon','honom','hundra','hundraen','hundraett','hur','i','ibland','idag','igår','igen','imorgon','in','inför','inga','ingen','ingenting','inget','innan','inne','inom','inte','inuti','ja','jag','jämfört','kan','kanske','knappast','kom','komma','kommer','kommit','kr','kunde','kunna','kunnat','kvar','länge','längre','långsam','långsammare','långsammast','långsamt','längst','långt','lätt','lättare','lättast','legat','ligga','ligger','lika','likställd','likställda','lilla','lite','liten','litet','man','många','måste','med','mellan','men','mer','mera','mest','mig','min','mina','mindre','minst','mitt','mittemot','möjlig','möjligen','möjligt','möjligtvis','mot','mycket','någon','någonting','något','några','när','nästa','ned','nederst','nedersta','nedre','nej','ner','ni','nio','nionde','nittio','nittionde','nitton','nittonde','nödvändig','nödvändiga','nödvändigt','nödvändigtvis','nog','noll','nr','nu','nummer','och','också','ofta','oftast','olika','olikt','om','oss','över','övermorgon','överst','övre','på','rakt','rätt','redan','så','sade','säga','säger','sagt','samma','sämre','sämst','sedan','senare','senast','sent','sex','sextio','sextionde','sexton','sextonde','sig','sin','sina','sist','sista','siste','sitt','sjätte','sju','sjunde','sjuttio','sjuttionde','sjutton','sjuttonde','ska','skall','skulle','slutligen','små','smått','snart','som','stor','stora','större','störst','stort','tack','tidig','tidigare','tidigast','tidigt','till','tills','tillsammans','tio','tionde','tjugo','tjugoen','tjugoett','tjugonde','tjugotre','tjugotvå','tjungo','tolfte','tolv','tre','tredje','trettio','trettionde','tretton','trettonde','två','tvåhundra','under','upp','ur','ursäkt','ut','utan','utanför','ute','vad','vänster','vänstra','var','vår','vara','våra','varför','varifrån','varit','varken','värre','varsågod','vart','vårt','vem','vems','verkligen','vi','vid','vidare','viktig','viktigare','viktigast','viktigt','vilka','vilken','vilket','vill']
#STOP_WORDS2 = ['a','about','above','after','again','against','all','am','an','and','any','are','aren't','as','at','be','because','been','before','being','below','between','both','but','by','can't','cannot','could','couldn't','did','didn't','do','does','doesn't','doing','don't','down','during','each','e.g.','few','for','from','further','had','hadn't','has','hasn't','have','haven't','having','he','he'd','he'll','he's','her','here','here's','hers','herself','him','himself','his','how','how's','i','i'd','i'll','i'm','i've','if','in','into','is','isn't','it','it's','its','itself','let's','me','more','most','mustn't','my','myself','no','nor','not','of','off','on','once','only','or','other','ought','our','ours','ourselves','out','over','own','same','shan't','she','she'd','she'll','she's','should','shouldn't','so','some','such','than','that','that's','the','their','theirs','them','themselves','then','there','there's','these','they','they'd','they'll','they're','they've','this','those','through','to','too','under','until','up','very','was','wasn't','we','we'd','we'll','we're','we've','were','weren't','what','what's','when','when's','where','where's','which','while','who','who's','whom','why','why's','with','won't','would','wouldn't','you','you'd','you'll','you're','you've','your','yours','yourself','yourselves']
#~ STOP_WORDS += [' ','\n']

def cmp_len(x, y):
    if len(x) < len(y):
        return 1
    elif len(y) < len(x):
        return -1
    return 0

# TODO: Test how this method works over multiple databases. Yep, it leaks.
_fts_models = set()

class fts_fts(models.Model):
    _name = 'fts.fts'
    _order = "name, rank, count"

    name = fields.Char(string="Term",index=True)
    #~ res_model = fields.Many2one(comodel_name='ir.model')
    res_model = fields.Char()
    res_id = fields.Integer()
    count = fields.Integer(default=1)
    rank = fields.Integer(default=10)
    group_ids = fields.Many2many(comodel_name="res.groups")
    facet = fields.Selection([('term','Term'),('author','Author')], string='Facet')

    @api.model
    def register_fts_model(self, model):
        _fts_models.add(model)

    @api.model
    def get_fts_models(self):
        return _fts_models

    @api.model
    def fts_search(self, query, domain=[], models=None, limit=None, offset=0):
        models = models or self.get_fts_models()
        results = []
        for model in models:
            res = self.env[model].fts_search(query, domain=domain)
            for d in res:
                d['model'] = model
            results += res
        results.sort(lambda x, y: (x['ts_rank'] > y['ts_rank'] and 1) or (x['ts_rank'] < y['ts_rank'] and -1) or 0)
        if offset:
            results = results[offset:]
        if limit:
            results = results[:limit]
        return results
        
    @api.model
    def update_fts_search_terms(self):
        """Update all search terms for objects marked as dirty, up to the maximum time limit. Default setting is for a cron job with a 5 minute interval."""
        _logger.info('Starting FTS update')
        count = 0
        start = datetime.now()
        limit = timedelta(minutes=float(self.env['ir.config_parameter'].get_param('website_fts.time_limit', '4.5')))
        for model in _fts_models:
            records = self.env[model].search([('fts_dirty', '=', True)], order='create_date asc')
            _logger.info('Updating FTS terms for %s(%s%s)' % (records._name, ', '.join([str(id) for id in records._ids[:10]]), ('... [%s more]' % (len(records._ids) -10)) if len(records._ids) > 10 else ''))
            for record in records:
                try:
                    record._full_text_search_update()
                    count += 1
                    # Commit to avoid locking rows for the full duration of this function.
                    self.env.cr.commit()
                except:
                    _logger.warn("Could not update FTS terms for %s" % record)
                    self.log_error('DEBUG')
                if datetime.now() - start > limit:
                    _logger.info('Time limit reached. Processed %s records. Last record to be processed was %s' % (count, record))
                    return
        _logger.info('Finished FTS update for all records')

    @api.one
    @api.depends('res_model','res_id')
    def _model_record(self):
        if self.res_model and self.res_id and self.env[self.res_model].browse(self.res_id):
            self.model_record = self.env[self.res_model].browse(self.res_id)
            #~ self.model_record = (self.res_model,self.res_id)
        else:
            self.model_record = None

    @api.model
    def _reference_models(self):
        models = self.env['ir.model'].search([('state', '!=', 'manual')])
        return [(model.model, model.name) for model in models if (not model.model.startswith('ir.') or model.model in ['ir.attachment', 'ir.ui.view'])]
    model_record = fields.Reference(string="Record", selection="_reference_models", compute="_model_record", store=True) # ,store=True,index=True)

    @api.model
    def get_text(self, texts, words):
        text = ''
        for t in texts:
            text += ' '.join(BeautifulSoup(t, 'html.parser').findAll(text=True))
        return text

    @api.model
    def clean_punctuation(self, text):
        return text.rstrip(',').rstrip('.').rstrip(':').rstrip(';').rstrip('!')

    @api.model
    def update_html(self, res_model, res_id, html='', groups=None, facet='term', rank=10):
        self.env['fts.fts'].search([('res_model', '=', res_model), ('res_id', '=', res_id), ('facet', '=', facet)]).unlink()
        soup = BeautifulSoup(html.strip().lower(), 'html.parser') #decode('utf-8').encode('utf-8')
        texts = [self.clean_punctuation(w) for w in ' '.join([w.rstrip(',') for w in soup.findAll(text=True) if not w in STOP_WORDS + [';','=',':','(',')',' ','\n']]).split(' ')]
        for word, count in Counter(texts).items():
            if word:
                self.env['fts.fts'].create({'res_model': res_model,'res_id': res_id, 'name': '%.30s' % word.lower(),'count': count,'facet': facet,'rank': rank, 'group_ids': [(6, 0, [g.id for g in groups or []])]})

    @api.model
    def update_text(self, res_model, res_id, text='', groups=None, facet='term', rank=10):
        text = text or ''
        #~ self.env['fts.fts'].search([('res_model', '=', res_model), ('res_id', '=', res_id), ('facet', '=', facet)]).unlink() #this remove term in each call
        text = text.strip().lower().split(' ')
        texts = [self.clean_punctuation(w) for w in ' '.join([w.rstrip(',') for w in text if not w in STOP_WORDS + [' ','\n']]).split(' ')]
        for word, count in Counter(texts).items():
            if word:
                self.env['fts.fts'].create({'res_model': res_model,'res_id': res_id, 'name': '%.30s' % word.lower(),'count': count,'facet': facet,'rank': rank, 'group_ids': [(6, 0, [g.id for g in groups or []])]})

    def word_union(self, r1, r2):
        r3 = self.env['fts.fts'].browse([])
        for r11 in r1:
            for r21 in r2:
                if r21.model_record == r11.model_record:
                    r3 |= r11
        return r3



    @api.model
    def term_search(self, search, facet=None, res_models=None, limit=5, offset=0):
        if res_models == None:
            res_models = ['product.template', 'product.product', 'blog.post']
        start = datetime.now()
        word_list = []
        if '"' in search:
            for w in search.split('"'):
                if w.strip() != '':
                    word_list.append(w)
        else:
            word_list = search.split(' ')
        # Sort by longest (probably most significant) word first.
        word_list.sort(cmp_len)

# 1) get list of models for first search
# 2) search each word within the ever reduced list of models
# the model-list has to be complete, limit can only be applied at end
# TODO: save number of words found for each model_record to have an impact for rank

        word_rank = {}
        words = {}
        for w in word_list:
            domain = [
                ('name', 'like', '%%%s%%' % w),
                ('model_record', '!=', False),
                '|',
                    ('group_ids', '=', False),
                    ('group_ids', 'in', [g.id for g in self.env.user.groups_id])
            ]
            if res_models:
                if isinstance(res_models, list):
                    for m in res_models:
                        domain.append(('res_model', 'in', res_models))
                else:
                    domain.append(('res_model', '=', res_model))
            if words:
                domain.append(('model_record', 'in', words.keys()))
            _logger.debug(domain)
            # Create updated list of matching terms
            words2 = {}
            for term in self.env['fts.fts'].search_read(domain, ['model_record', 'rank']):
                if term['model_record'] in words:
                    # A match to the same record is already in the list. Compare ranks and keep the lowest match.
                    if term['rank'] < words[term['model_record']]['rank']:
                        words2[term['model_record']] = {
                            'id': term['id'],
                            'rank': term['rank'],
                        }
                    else:
                        words2[term['model_record']] = words[term['model_record']]
                else:
                    # No previous match in the list. Add this one.
                    words2[term['model_record']] = {
                        'id': term['id'],
                        'rank': term['rank'],
                    }
            # Replace the previous words with the updated version
            words = words2
            if not words:
                break
            _logger.debug(words)
        words = self.env['fts.fts'].browse([words[w]['id'] for w in words]).sorted(key=lambda r: r.rank)
        _logger.debug('words: %s' % words)


        facets = []

        for f in set(words.mapped('facet')):
            w,c = Counter(words.filtered(lambda w: w.facet == f)).items()[0]
            facets.append((w.facet,c))
        models = []
        for m in set(words.mapped('res_model')):
            w,c = Counter(words.filtered(lambda w: w.res_model == m)).items()[0]
            models.append((w.res_model,c))
        delta_t = datetime.now() - start
        _logger.info('FTS search (%s) took %.2f s' % (search, (delta_t.seconds + (delta_t.microseconds / 1000000.0))))
        return {'terms': words,'facets': facets,'models': models, 'docs': words.filtered(lambda w: w.model_record != False).mapped('model_record')[:limit]}


    @api.one
    def get_object(self,words):
        #~ _logger.warn('get_object')
        if self.res_model == 'ir.ui.view':
            page = self.env['ir.ui.view'].browse(self.res_id)
            return {'name': page.name, 'body': self.get_text([page.arch],words)}
        return {'name': '<none>', 'body': '<empty>'}

    @api.model
    def log_error(self, level='DEBUG'):
        e = sys.exc_info()
        _logger.log(getattr(logging, level), ''.join(traceback.format_exception(e[0], e[1], e[2])))

class fts_model(models.AbstractModel):
    """
    Inherit this model to make a model searchable through the FTS.
    
    All inheriting models need to define the fields that should be used to build the searchable document.
    Override _fts_trigger and make it depend on all fields that make up the document.
    """

    _name = 'fts.model'
    _description = 'FTS Model'

    _fts_fields = []
    _fts_fields_d = []
    # {
    #     'name': field_name,
    #     ['weight': 'A' / 'B' / 'C' / 'D',]
    #     ['related': related_field_name (e.g. 'foo_id.bar'),]
    #     ['related_table': related_table_name,]
    #     ['trigger_only': True / False,]
    # }
    
    # name: the name of the field to be used in fts.
    # weight: A label for weighting search results. A > B > C > D.
    # trigger_only: Only use this field to trigger recompute. Field should not be used to build the searchable document.

    fts_dirty = fields.Boolean(string='Dirty', help='FTS terms for this record need to be updated', default=True)
    _fts_trigger = fields.Boolean(string='Trigger FTS Update', help='Change this field to update FTS.', compute='_compute_fts_trigger', store=True)

    @api.one
    def _compute_fts_trigger(self):
        """
        Dummy field to trigger the updates on SQL level. Tracking
        changes is much easier on Odoo level than on SQL level. Make
        this field dependant on the relevant fields.
        """
        # TODO: Trigger this update when relevant translations change.
        if self._fts_trigger:
            self._fts_trigger = True
        else:
            self._fts_trigger = False

    @api.model
    def _lang_o2pg(self, lang):
        """
        Return the corresponding name of the language in postgresql.
        """
        langs = {}
        return langs.get(lang, 'swedish')

    @api.model
    def _get_fts_vector_expr_old(self):
        fields = []
        for field in self._fts_fields_d:
            if not field.get('trigger_only'):
                fields.append("        setweight(to_tsvector('english', COALESCE(%s,'')), '%s')" % (field['name'], field.get('weight', 'D')))
        return ' ||\n'.join(fields)

    @api.model
    def _get_fts_vector_expr(self):
        def field2sql_expr(name):
            field = self.fields_get([name])[name]
            if field.get('related'):
                rel_name = field['related'][0]
                # TODO: What about more than one level? Is that possible?
                #rel_field = self.fields_get([rel_name])
                return '"%s_%s"."%s"' % (self._table, rel_name, name)
            return '"%s"."%s"' % (self._table, name)
        fields = []
        for field in self._fts_fields_d:
            if not field.get('trigger_only'):
                fields.append('''        setweight(to_tsvector("english", COALESCE(%s,"")), "%s")''' % (field2sql_expr(field['name']), field.get('weight', 'D')))
        return ' ||\n'.join(fields)

    def _auto_init(self, cr, context=None):
        """

        Call _field_create and, unless _auto is False:

        - create the corresponding table in database for the model,
        - possibly add the parent columns in database,
        - possibly add the columns 'create_uid', 'create_date', 'write_uid',
          'write_date' in database if _log_access is True (the default),
        - report on database columns no more existing in _columns,
        - remove no more existing not null constraints,
        - alter existing database columns to match _columns,
        - create database tables to match _columns,
        - add database indices to match _columns,
        - save in self._foreign_keys a list a foreign keys to create (see
          _auto_end).

        """
        res = super(fts_model, self)._auto_init(cr, context)
        columns = self._select_column_data(cr)
        if self._auto and self._fts_fields_d and '_fts_trigger' in columns:
            update_index = False
            if '_fts_vector' not in columns:
                # Add _fts_vector column to the table
                cr.execute('ALTER TABLE "%s" ADD COLUMN "_fts_vector" tsvector' % self._table)
                update_index = True

            #~ # Create data to handle triggers on all related tables.
            #~ triggers = {}
            #~ for field in self._fts_fields_d:
                #~ if field.get('related'):
                    #~ table = field['related_table']
                    #~ name = field['related']
                #~ else:
                    #~ table = self._table
                    #~ name = field['name']
                #~ if table not in triggers:
                    #~ triggers[table] = []
                #~ triggers[table].append(name)
            #~ # Drop all old triggers.
            #~ for trigger in triggers:
                #~ if trigger == self._table:
                    #~ tname = 'upd_fts_vector'
                #~ else:
                    #~ tname = 'upd_fts_vector_%s' % self._table
                #~ cr.execute("DROP TRIGGER IF EXISTS %s ON %s;" % tname, trigger)
            cr.execute("DROP TRIGGER IF EXISTS upd_fts_vector ON %s;" % self._table)
            
            # Create function that updates the new _fts_vector column.
            func_name = '%s_fts_vector_trigger' % self._table
            cr.execute("DROP FUNCTION IF EXISTS %s();" % func_name)
            fields = []
            _logger.warn('_fts_fields_d %s: %s' % (self._table, self._fts_fields_d))
            for field in self._fts_fields_d:
                if field.get('sql'):
                    fields.append(field['sql'])
                elif field.get('related'):
                    fields.append("        setweight(to_tsvector('swedish', COALESCE((SELECT %s FROM %s WHERE id = new.%s), '')), '%s')" % (
                        field['related'].split('.')[1],
                        field['related_table'],
                        field['related'].split('.')[0],
                        field.get('weight', 'D')))
                else:
                    fields.append("        setweight(to_tsvector('swedish', COALESCE(new.%s, '')), '%s')" % (field['name'], field.get('weight', 'D')))
            fields = ' ||\n'.join(fields) + ';'
            expr = "CREATE FUNCTION %s() RETURNS trigger AS $$\n" \
            "begin\n" \
            "    new._fts_vector :=%s\n" \
            "    return new;\n" \
            "end\n" \
            "$$ LANGUAGE plpgsql;" % (func_name, fields)
            _logger.debug(expr)
            cr.execute(expr)
            # Bind the update function to a trigger.
            #~ fields = []
            #~ for field in self._fts_fields_d:
                #~ fields.append(field['name'])
            #~ fields = ', '.join(fields)

            #~ # Create triggers on relevant tables.
            #~ for table in triggers:
                #~ if table == self._table:
                    #~ tname = 'upd_fts_vector'
                #~ else:
                    #~ tname = 'upd_fts_vector_%s' % self._table
                #~ expr = "CREATE TRIGGER %s BEFORE INSERT OR UPDATE OF %s ON %s " \
                #~ "FOR EACH ROW EXECUTE PROCEDURE %s();" % (tname, ', '.join(triggers[table]), table, func_name)
                #~ _logger.debug(expr)
                #~ cr.execute(expr)
            expr = "CREATE TRIGGER upd_fts_vector BEFORE INSERT OR UPDATE OF _fts_trigger ON %s " \
                "FOR EACH ROW EXECUTE PROCEDURE %s();" % (self._table, func_name)
            _logger.debug(expr)
            cr.execute(expr)
            if update_index:
                # Create index on the _fts_vector column.
                cr.execute("CREATE INDEX %s_fts_vector_idx ON %s USING GIST (_fts_vector);" % (self._table, self._table))
        return res

    @api.model
    def _fts_reindex(self):
        expr = "REINDEX INDEX %s_fts_vector_idx;" % self._table
        _logger.debug(expr)
        self.env.cr.execute(expr)

    @api.model
    def _fts_update_vector(self):
        _logger.debug('Updating FTS for %s' % self._name)
        expr = "SELECT id FROM %s WHERE _fts_trigger in (false, NULL);" % self._table
        _logger.debug(expr)
        self.env.cr.execute(expr)
        f_ids = [d['id'] for d in self.env.cr.dictfetchall()]
        expr = "SELECT id FROM %s WHERE _fts_trigger = true;" % self._table
        _logger.debug(expr)
        self.env.cr.execute(expr)
        t_ids = [d['id'] for d in self.env.cr.dictfetchall()]
        if f_ids:
            expr = "UPDATE  %s SET _fts_trigger = true WHERE id in %%s;" % self._table
            _logger.debug(expr)
            _logger.debug(f_ids)
            self.env.cr.execute(expr, [tuple(f_ids)])
        if t_ids:
            expr = "UPDATE  %s SET _fts_trigger = false WHERE id in %%s;" % self._table
            _logger.debug(expr)
            _logger.debug(t_ids)
            self.env.cr.execute(expr, [tuple(t_ids)])

    @api.model
    def _fts_get_lexemes(self, query):
        """
        Convert raw user input to an FTS ready expression.
        :param query: Search string.
        :return: List of search terms (lexemes).
        """
        # TODO: Find all excluded chars. Replace to not ruin query?
        # ! = not, & = and, | = or
        # \ = escape char. escape all weird chars?
        escape = string.punctuation
        for c in escape:
            query = query.replace(c, '\\%s' % c)
        query = [('%s:*' % x.strip()) for x in query.split(' ') if x.strip()]
        return query

    @api.model
    def _fts_get_where_clause(self, query):
        """Inheritable function to get any extra expressions and values for the FTS search WHERE clause.
        Example: return ["website_published = %s"], [True]
        """
        return [], []

    @api.model
    def fts_search(self, query, domain=[]):
        """
        Perform an FTS search.
        :param query: The raw search string.
        :param domain: An optional Odoo search domain.
        :return: a list of dicts with ids and weights ([[{'id': 1, 'ts_rank': 0.23}]).
        """
        # TODO: Check access rights and rules. Look at _search() and _apply_ir_rules() in models.
        #self.check_access_rights(cr, access_rights_uid or user, 'read')
        self.check_access_rights('read')
        # TODO: Clean query from problematic characters.
        lexemes = self._fts_get_lexemes(query)
        lexemes = ' & '.join(lexemes)
        query = self._where_calc(domain)
        self._apply_ir_rules(query, 'read')
        #where, values = self._fts_get_where_clause(query)
        query.where_clause.append('''"%s"."%s" @@ to_tsquery('swedish', %%s)''' % (self._table, '_fts_vector'))
        query.where_clause_params.append(lexemes)
        from_clause, where_clause, params = query.get_sql()
        params = [lexemes] + params
        expr = '''SELECT "%s"."id", ts_rank("%s"."%s", to_tsquery('swedish', %%s)) FROM %s WHERE %s;''' % (self._table, self._table, '_fts_vector', from_clause, where_clause)
        _logger.debug(expr)
        _logger.debug(params)
        self.env.cr.execute(expr, params)
        res = {}
        results = self.env.cr.dictfetchall()
        _logger.debug(results)
        #~ for d in results:
            #~ res[d['id']] = d['ts_rank']
        return results

    @api.model
    def fts_search_browse(self, query, domain=[]):
        """
        Perform an FTS search. Returns a recordset sorted by weight.
        """
        # TODO: Fix sorting.
        res = self.fts_search(query, domain)
        return self.browse([d['id'] for d in res])

    @api.model
    def _setup_complete(self):
        """
        Register this model as an FTS model.
        """
        # TODO: Stop leaking between databases.
        res = super(fts_model, self)._setup_complete()
        _logger.warn('_setup_complete %s' % self._name)
        if self._name != 'fts.model':
            self.env['fts.fts'].register_fts_model(self._name)
        return res

    @api.multi
    def _full_text_search_delete(self):
        terms = self.env['fts.fts'].search(['|' for i in range(len(self._ids) - 1)] + [('model_record', '=', '%s,%s' % (self._name, id)) for id in self._ids])
        if terms:
            terms.unlink()

    @api.one
    def _full_text_search_update(self):
        self._full_text_search_delete()
        self.fts_dirty = False

    #~ @api.model
    #~ @api.returns('self', lambda value: value.id)
    #~ def create(self, vals):
        #~ res = super(fts_model, self).create(vals)
        #~ res._full_text_search_update()
        #~ return res

    @api.multi
    def write(self, vals):
        for f in self._fts_fields:
            if f in vals:
                vals['fts_dirty'] = True
            break
        return super(fts_model, self).write(vals)

    @api.multi
    def unlink(self):
        self._full_text_search_delete()
        return super(fts_model, self).unlink()

class fts_website(models.Model):
    _name = 'fts.website'

    name = fields.Char(string="Url")
    xml_id = fields.Char()
    body = fields.Text()
    group_ids = fields.Many2many(comodel_name="res.groups")
    res_id = fields.Integer()


class view(models.Model):
    _name = 'ir.ui.view'
    _inherit = ['ir.ui.view', 'fts.model']

    _fts_fields = ['arch', 'groups_id']
    _fts_fields_d = [{'name': 'arch'}]

    @api.depends('arch')
    @api.one
    def _compute_fts_trigger(self):
        """
        Dummy field to trigger the updates on SQL level. Tracking
        changes is much easier on Odoo level than on SQL level. Make
        this field dependant on the relevant fields.
        """
        # TODO: Trigger this update when relevant translations change.
        if self._fts_trigger:
            self._fts_trigger = True
        else:
            self._fts_trigger = False

    @api.one
    def _full_text_search_update(self):
        super(view, self)._full_text_search_update()
        if self.type == 'qweb' and 't-call="website.layout"' in self.arch:
            website = self.env['fts.website'].search([('res_id','=',self.id)])
            if website:
                website.write({'name': self.name, 'xml_id': self.xml_id, 'body': self.env['fts.fts'].get_text([self.arch],[]), 'res_id': self.id, 'group_ids': self.groups_id })
            else:
                website = self.env['fts.website'].create({'name': self.name, 'xml_id': self.xml_id, 'body': self.env['fts.fts'].get_text([self.arch],[]), 'res_id': self.id, 'group_ids': self.groups_id })
            self.env['fts.fts'].update_html('fts.website',website.id,html=website.body,groups=website.group_ids)

class WebsiteFullTextSearch(http.Controller):

    @http.route(['/search'], type='http', auth="public", website=True)
    def search_page(self, search_advanced=False, search_on_pages=True, search_on_blogposts=True, search_on_comments=True, search_on_customers=True,
                       search_on_jobs=True, search_on_products=True, case_sensitive=False, search='', **post):
        #~ _logger.warn(isinstance(search_on_pages, unicode))
        # Process search parameters
        if isinstance(search_on_pages, unicode):
            self._search_on_pages=self._normalize_bool(search_on_pages)
        if isinstance(search_on_blogposts, unicode):
            self._search_on_blogposts=self._normalize_bool(search_on_blogposts)
        if isinstance(search_on_comments, unicode):
            self._search_on_comments=self._normalize_bool(search_on_comments)
        if isinstance(search_on_customers, unicode):
            self._search_on_customers=self._normalize_bool(search_on_customers)
        if isinstance(search_on_jobs, unicode):
            self._search_on_jobs=self._normalize_bool(search_on_jobs)
        if isinstance(search_on_products, unicode):
            self._search_on_products=self._normalize_bool(search_on_products)
        if isinstance(case_sensitive, unicode):
            self._case_sensitive=self._normalize_bool(case_sensitive)
        self._search_advanced=False

        user = request.registry['res.users'].browse(request.cr, request.uid, request.uid, context=request.context)
        values = {'user': user,
                  'is_public_user': user.id == request.website.user_id.id,
                  'header': post.get('header', dict()),
                  'searches': post.get('searches', dict()),
                  'results_count': 0,
                  'results': dict(),
                  'pager': None,
                  'search_on_pages': self._search_on_pages,
                  'search_on_blogposts': self._search_on_blogposts,
                  'search_on_comments': self._search_on_comments,
                  'search_on_customers': self._search_on_customers,
                  'search_on_jobs': self._search_on_jobs,
                  'search_on_products': self._search_on_products,
                  'case_sensitive': self._case_sensitive,
                  'search_advanced': False,
                  'sorting': False,
                  'search': search
                  }
        #~ _logger.warn(values)
        return request.website.render("website_fts.search_page", values)

    @http.route(['/search_results'], type='http', auth="public", website=True)
    def search_result(self, search='', times=0, **post):
        vals = request.env['fts.fts'].term_search(search)
        vals['kw'] = search
        return request.website.render("website_fts.search_result", vals)

    @http.route(['/search_suggestion'], type='json', auth="public", website=True)
    def search_suggestion(self, search='', facet=None, res_model=None, limit=0, offset=0, **kw):
        result = request.env['fts.fts'].fts_search(search, [], res_model, limit, offset)
        result_models = {}
        for model in request.env['fts.fts'].get_fts_models():
            ids = []
            for res in result:
                if res['model'] == model:
                    ids.append(res['id'])
            if ids:
                result_models[model] = request.env[model].browse(ids)
        result_list = []
        for record in result:
            result_list.append(res_models[record['model']].filtered(lambda r: r.id == record['id']))
        rl = []
        i = 0
        while i < len(result_list) and len(rl) < 5:
            r = result_list[i]
            if r._name in ['product.template', 'product.public.category']:
                rl.append({
                    'res_id': r.id,
                    'model_record': r._name,
                    'name': r.name,
                })
            elif r._name == 'product.product':
                rl.append({
                    'res_id': r.id,
                    'model_record': r._name,
                    'name': r.model_record.name,
                    'product_tmpl_id': r.product_tmpl_id.id,
                })
            elif r._name == 'blog.post':
                rl.append({
                    'res_id': r.id,
                    'model_record': r._name,
                    'name': r.model_record.name,
                    'blog_id': r.blog_id.id,
                })
            elif r._name == 'product.facet.line':
                rl.append({
                    'res_id': r.id,
                    'model_record': r._name,
                    'product_tmpl_id': r.product_tmpl_id.id,
                    'product_name': r.product_tmpl_id.name,
                })
            i += 1
        return rl
        
        #~ result = request.env['fts.fts'].term_search(search.lower(), facet, res_model, limit, offset)
        #~ #_logger.warn(result)
        #~ result_list = result['terms']
        #~ rl = []
        #~ i = 0
        #~ while i < len(result_list) and len(rl) < 5:
            #~ r = result_list[i]
            #~ if r.model_record._name in ['product.template', 'product.public.category']:
                #~ rl.append({
                    #~ 'res_id': r.res_id,
                    #~ 'model_record': r.model_record._name,
                    #~ 'name': r.model_record.name,
                #~ })
            #~ elif r.model_record._name == 'product.product':
                #~ rl.append({
                    #~ 'res_id': r.res_id,
                    #~ 'model_record': r.model_record._name,
                    #~ 'name': r.model_record.name,
                    #~ 'product_tmpl_id': r.model_record.product_tmpl_id.id,
                #~ })
            #~ elif r.model_record._name == 'blog.post':
                #~ rl.append({
                    #~ 'res_id': r.res_id,
                    #~ 'model_record': r.model_record._name,
                    #~ 'name': r.model_record.name,
                    #~ 'blog_id': r.model_record.blog_id.id,
                #~ })
            #~ elif r.model_record._name == 'product.facet.line':
                #~ rl.append({
                    #~ 'res_id': r.res_id,
                    #~ 'model_record': r.model_record._name,
                    #~ 'product_tmpl_id': r.model_record.product_tmpl_id.id,
                    #~ 'product_name': r.model_record.product_tmpl_id.name,
                #~ })
            #~ i += 1
        #~ return rl

class fts_test_model(models.Model):
    _name = 'fts.test.model'
    _description = 'FTS Test Wizard Models'

    name = fields.Char(string='Name')

class fts_test(models.TransientModel):
    _name = 'fts.test'
    _description = 'FTS Test Wizard'

    @api.model
    def _default_fts_model_ids(self):
        for model in _fts_models:
            obj = self.env['fts.test.model'].search([('name', '=', model)])
            if not obj:
                self.env['fts.test.model'].create({'name': model})

    search = fields.Char(string='Search Term')
    type = fields.Selection([('old', 'Old'), ('new', 'New')], default='old')
    fts_ids = fields.Many2many(string='Search Results', comodel_name='fts.fts')
    fts_model_ids = fields.Many2many(comodel_name='fts.test.model', string='Models', default=_default_fts_model_ids)
    user_id = fields.Many2one(string='User', comodel_name='res.users')
    log = fields.Html(string='Log', readonly=True, default="""<table class="table table-striped">
  <thead>
    <tr>
      <th>Type</th>
      <th>Time</th>
      <th>Search Term</th>
      <th>Models</th>
      <th># Hits</th>
    </tr>
  </thead>
  <tbody>
  </tbody>
</table>""")
    results = fields.Html(string='Search Results', readonly=True, default="""<table class="table table-striped">
  <thead>
    <tr>
      <th>Rank</th>
      <th>Search Term</th>
      <th>Name</th>
      <th>Model</th>
      <th>Id</th>
    </tr>
  </thead>
  <tbody>
  </tbody>
</table>""")

    @api.one
    @api.onchange('search')
    def test_search(self):
        if self.search:
            start = datetime.now()
            if self.type == 'old':
                if self.user_id:
                    result = self.env['fts.fts'].sudo(self.user_id.id).term_search(self.search.lower(), res_models=[m.name for m in self.fts_model_ids])
                else:
                    result = self.env['fts.fts'].term_search(self.search.lower(), res_models=[m.name for m in self.fts_model_ids])
                delta_t = datetime.now() - start
                self.fts_ids = [(6, 0, [r.id for r in result['terms']])]
                rows = self.log.split('\n')
                self.log = '\n'.join(
                    rows[:-2] + [
                        '    <tr><td>Old</td><td>%.2f s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                            (delta_t.seconds + (delta_t.microseconds / 1000000.0)),
                            self.search,
                            ', '.join([m.name for m in self.fts_model_ids]),
                            len(self.fts_ids)
                    )] + rows[-2:])
            elif self.type == 'new':
                count = 0
                rows = self.results.split('\n')
                self.results = '\n'.join(
                    rows[:11] + rows[-2:])
                for model in self.fts_model_ids:
                    if self.user_id:
                        result = self.env[model.name].sudo(self.user_id.id).fts_search_browse(self.search)
                    else:
                        result = self.env[model.name].fts_search_browse(self.search)
                    count += len(result)
                    rows = self.results.split('\n')
                    self.results = '\n'.join(
                        rows[:-2] + [
                            ('    <tr><td>N/A</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                                self.search, r.name, r._model, r.id
                        )) for r in result] + rows[-2:])
                        
                delta_t = datetime.now() - start
                rows = self.log.split('\n')
                self.log = '\n'.join(
                    rows[:-2] + [
                        '    <tr><td>New</td><td>%.2f s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                            (delta_t.seconds + (delta_t.microseconds / 1000000.0)),
                            self.search,
                            ', '.join([m.name for m in self.fts_model_ids]),
                            count
                    )] + rows[-2:])

<%inherit file="base.mako"/>

#<%def name="preview()">${c['value'] or '-'}</%def>

<%def name="table_body(c, lang)">
    <tr><td width="150" valign="top">${_('tt_ch.bakom.versorgungsgebiet_prog')}</td><td>${c['value']}</td></tr>
</%def>


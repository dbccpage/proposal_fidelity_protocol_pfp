-- Preserve literal code characters and permit long identifiers to wrap in PDF.
function Code(code)
  if not FORMAT:match('latex') then
    return nil
  end
  local escaped = {
    ['\\'] = '\\textbackslash{}', ['{'] = '\\{', ['}'] = '\\}',
    ['$'] = '\\$', ['%'] = '\\%', ['&'] = '\\&', ['#'] = '\\#',
    ['_'] = '\\_', ['^'] = '\\textasciicircum{}', ['~'] = '\\textasciitilde{}'
  }
  local text = code.text:gsub('[\\{}$%%&#_^~]', escaped)
  if code.text:match('^%x+$') and #code.text >= 32 then
    return pandoc.RawInline('latex', '\\texttt{\\seqsplit{' .. text .. '}}')
  end
  text = text:gsub('\\_', '\\_\\allowbreak{}')
             :gsub('/', '/\\allowbreak{}'):gsub('%-', '-\\allowbreak{}')
  return pandoc.RawInline('latex', '\\texttt{' .. text .. '}')
end

-- Long evidence identifiers must remain readable inside manuscript tables.
function Code(element)
  if FORMAT:match('latex') and #element.text > 24
     and element.text:match('^[A-Za-z0-9_./: %-]+$') then
    return pandoc.RawInline('latex', '\\nolinkurl{' .. element.text .. '}')
  end
end

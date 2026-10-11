-- Plan 030 theme filter (ported from py4kids' panels.lua): chapter kickers, framed code,
-- the teacher "Answers" panel, inline-code break points, and the DejaVu fallback for glyphs the
-- primary fonts lack.
local names = {answers=true}
local function fallback_glyph(cp)
  return (cp >= 0x2190 and cp <= 0x21ff) or (cp >= 0x0370 and cp <= 0x03ff) or
    (cp >= 0x2200 and cp <= 0x22ff) or (cp >= 0x2500 and cp <= 0x25ff) or
    cp == 0x2610 or cp == 0x2713 or cp == 0x2717
end
local escaped = {
  ['\\'] = '\\textbackslash{}', ['{'] = '\\{', ['}'] = '\\}',
  ['$'] = '\\$', ['%'] = '\\%', ['&'] = '\\&', ['#'] = '\\#',
  ['_'] = '\\_', ['^'] = '\\textasciicircum{}', ['~'] = '\\textasciitilde{}',
}
function Header(el)
  if not FORMAT:match('latex') then return nil end
  -- Quarto gives the heading-less the-index.qmd an empty chapter: drop it (\printindex opens one).
  if el.level == 1 and #el.content == 0 then return {} end
  if (el.level == 3 or el.level == 4) and el.content[1] then
    local title = pandoc.utils.stringify(el.content)
    if title:match('^Practice ') or title:match('^Solution') then
      return {pandoc.RawBlock('latex', '\\Needspace{12\\baselineskip}'), el}
    end
  end
  if el.level ~= 1 then return nil end
  local label = el.attributes['pub-label']
  if label == nil then return nil end
  local prefix = ''
  if el.attributes['pub-mainmatter'] == 'true' then prefix = '\\mainmatter\n' end
  prefix = prefix .. '\\pubchapterlabel{' .. label .. '}'
  el.attributes['pub-label'] = nil
  el.attributes['pub-mainmatter'] = nil
  return {pandoc.RawBlock('latex', prefix), el}
end
function Div(el)
  for _, class in ipairs(el.classes) do
    if names[class] then
      local blocks = {pandoc.RawBlock('latex', '\\begin{pub' .. class .. '}')}
      for _, block in ipairs(el.content) do table.insert(blocks, block) end
      table.insert(blocks, pandoc.RawBlock('latex', '\\end{pub' .. class .. '}'))
      return blocks
    end
  end
end
function CodeBlock(el)
  if not FORMAT:match('latex') then return nil end
  return {pandoc.RawBlock('latex', '\\begin{pubcode}'), el,
          pandoc.RawBlock('latex', '\\end{pubcode}')}
end
function Str(el)
  if not FORMAT:match('latex') then return nil end
  local changed = false
  local out = {}
  for _, cp in utf8.codes(el.text) do
    local char = utf8.char(cp)
    if fallback_glyph(cp) then
      changed = true
      table.insert(out, '{\\fallbackfont ' .. char .. '}')
    else
      table.insert(out, escaped[char] or char)
    end
  end
  if changed then return pandoc.RawInline('latex', table.concat(out)) end
  return nil
end
function Code(el)
  if not FORMAT:match('latex') then return nil end
  local parts = {}
  local run = 0
  local chars = {}
  for _, cp in utf8.codes(el.text) do table.insert(chars, cp) end
  -- Break points (py4kids plan 099 A3): after `\ _ ( ) , : / + - =`, or inside a run of 12
  -- letters and digits; never before a space or between two punctuation characters.
  for i, cp in ipairs(chars) do
    local c = utf8.char(cp)
    local following = chars[i + 1] and utf8.char(chars[i + 1]) or nil
    if fallback_glyph(cp) then
      table.insert(parts, '{\\fallbackfont ' .. c .. '}')
    else
      table.insert(parts, escaped[c] or c)
    end
    if c:match('[A-Za-z0-9]') then run = run + 1 else run = 0 end
    local open = following ~= nil and not following:match('^[%p%s]$')
    if c == ',' or c == ':' then open = following ~= nil and not following:match('^%s$') end
    if open and c == '_' then open = following:match('^[A-Za-z0-9]$') ~= nil end
    if open and (c == '\\' or c:match('[_%(%)%,%:%/%+%-%=]') or run >= 12) then
      table.insert(parts, '\\allowbreak{}')
      run = 0
    end
  end
  return pandoc.RawInline('latex', '\\texttt{' .. table.concat(parts) .. '}')
end
-- A display equation wider than the line is scaled down to fit (never overflows the margin).
function Math(el)
  if not FORMAT:match('latex') or el.mathtype ~= 'DisplayMath' then return nil end
  return pandoc.RawInline('latex', '\\[\\adjustbox{max width=\\linewidth}{$\\displaystyle ' ..
    el.text .. '$}\\]')
end
return {{Header = Header, Div = Div, CodeBlock = CodeBlock, Str = Str, Code = Code, Math = Math}}

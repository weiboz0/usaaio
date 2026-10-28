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
-- Inline code as LaTeX with break points. Everywhere (py4kids plan 099 A3, Plan 033 D3 (b)):
-- after `\ _ ( ) , : / + - =`, after `.` before a letter or digit (not inside a decimal number
-- such as `0.05`), or inside a run of 12 letters and digits; never before a space or between two
-- punctuation characters. In a table cell
-- (`in_table`), also before `.`, `(`, `[` and `]` and after `[`, and the code is set at \small.
local function code_latex(text, in_table)
  local parts = {}
  local run = 0
  local chars = {}
  for _, cp in utf8.codes(text) do table.insert(chars, cp) end
  local just_broke = true -- no break before the first character
  for i, cp in ipairs(chars) do
    local c = utf8.char(cp)
    local following = chars[i + 1] and utf8.char(chars[i + 1]) or nil
    local previous = chars[i - 1] and utf8.char(chars[i - 1]) or nil
    local decimal_point = c == '.' and previous ~= nil and previous:match('^%d$') ~= nil and
      following ~= nil and following:match('^%d$') ~= nil
    if in_table and not just_broke and not decimal_point and c:match('^[%.%(%[%]]$') and
        previous ~= nil and not previous:match('^%s$') and previous ~= c then
      table.insert(parts, '\\allowbreak{}')
      run = 0
    end
    if fallback_glyph(cp) then
      table.insert(parts, '{\\fallbackfont ' .. c .. '}')
    else
      table.insert(parts, escaped[c] or c)
    end
    just_broke = false
    if c:match('[A-Za-z0-9]') then run = run + 1 else run = 0 end
    local open = following ~= nil and not following:match('^[%p%s]$')
    if c == ',' or c == ':' then open = following ~= nil and not following:match('^%s$') end
    if open and c == '_' then open = following:match('^[A-Za-z0-9]$') ~= nil end
    local dot = c == '.' and not decimal_point and following ~= nil and
      following:match('^[A-Za-z0-9]$') ~= nil
    local bracket = in_table and c == '[' and following ~= nil and not following:match('^%s$')
    if dot or bracket or
        (open and (c == '\\' or c:match('[_%(%)%,%:%/%+%-%=]') or run >= 12)) then
      table.insert(parts, '\\allowbreak{}')
      run = 0
      just_broke = true
    end
  end
  local body = '\\texttt{' .. table.concat(parts) .. '}'
  if in_table then return '{\\small' .. body .. '}' end
  return body
end
function Code(el)
  if not FORMAT:match('latex') then return nil end
  return pandoc.RawInline('latex', code_latex(el.text, false))
end
-- Plan 033 D3 (c): plain text in a table cell may break after `/` before a letter or digit, and
-- after `-` between two letters or digits. The text is split around raw \allowbreak{} so the
-- pieces stay Str and the main filter still escapes them.
local function table_str(el)
  local chars = {}
  for _, cp in utf8.codes(el.text) do table.insert(chars, utf8.char(cp)) end
  local out = {}
  local piece = {}
  for i, c in ipairs(chars) do
    table.insert(piece, c)
    local following = chars[i + 1]
    local previous = chars[i - 1]
    local alnum_after = following ~= nil and following:match('^[A-Za-z0-9]$') ~= nil
    if (c == '/' and alnum_after) or (c == '-' and alnum_after and previous ~= nil and
        previous:match('^[A-Za-z0-9]$')) then
      table.insert(out, pandoc.Str(table.concat(piece)))
      table.insert(out, pandoc.RawInline('latex', '\\allowbreak{}'))
      piece = {}
    end
  end
  if #out == 0 then return nil end
  if #piece > 0 then table.insert(out, pandoc.Str(table.concat(piece))) end
  return out
end
local function table_code(el)
  return pandoc.RawInline('latex', code_latex(el.text, true))
end
-- Plan 033 D3 (a): a table whose columns all have the default width gets wrapping relative
-- widths when its estimated natural width overflows the text block. Estimate: the longest cell
-- of each column at 0.6 em (6 pt at 10 pt) per character, against the edition's ~392 pt text
-- width. Widths follow each column's longest cell, with a floor of min(0.15, 0.5/ncols).
local CHAR_PT = 6
local TEXT_WIDTH_PT = 392
local function cell_rows(t)
  local rows = {}
  for _, row in ipairs(t.head.rows) do table.insert(rows, row) end
  for _, body in ipairs(t.bodies) do
    for _, row in ipairs(body.head) do table.insert(rows, row) end
    for _, row in ipairs(body.body) do table.insert(rows, row) end
  end
  for _, row in ipairs(t.foot.rows) do table.insert(rows, row) end
  return rows
end
local function column_lengths(t)
  local lengths = {}
  for i = 1, #t.colspecs do lengths[i] = 1 end
  for _, row in ipairs(cell_rows(t)) do
    local col = 1
    for _, cell in ipairs(row.cells) do
      local span = cell.col_span or 1
      if span == 1 and lengths[col] ~= nil then
        local text = pandoc.utils.stringify(cell.contents)
        lengths[col] = math.max(lengths[col], utf8.len(text) or #text)
      end
      col = col + span
    end
  end
  return lengths
end
local function relative_widths(lengths)
  local n = #lengths
  local floor = math.min(0.15, 0.5 / n)
  local fixed = {}
  -- Water-fill: columns whose proportional share is under the floor get the floor; the rest
  -- share what remains in proportion to their lengths. Repeat until no new column is floored.
  while true do
    local spare, total = 1, 0
    for i = 1, n do
      if fixed[i] then spare = spare - floor else total = total + lengths[i] end
    end
    local changed = false
    for i = 1, n do
      if not fixed[i] and spare * lengths[i] / total < floor then
        fixed[i] = true
        changed = true
      end
    end
    if not changed then
      local widths = {}
      for i = 1, n do
        widths[i] = fixed[i] and floor or spare * lengths[i] / total
      end
      return widths
    end
  end
end
local function fit_table(t)
  for _, spec in ipairs(t.colspecs) do
    if spec[2] ~= nil then return nil end
  end
  local lengths = column_lengths(t)
  local natural = 0
  for _, length in ipairs(lengths) do natural = natural + length * CHAR_PT end
  if natural <= TEXT_WIDTH_PT then return nil end
  local widths = relative_widths(lengths)
  local specs = {}
  for i, spec in ipairs(t.colspecs) do specs[i] = {spec[1], widths[i]} end
  t.colspecs = specs
  return t
end
local function Table(t)
  if not FORMAT:match('latex') then return nil end
  fit_table(t)
  return t:walk({Code = table_code, Str = table_str})
end
-- A display equation wider than the line is scaled down to fit (never overflows the margin).
function Math(el)
  if not FORMAT:match('latex') or el.mathtype ~= 'DisplayMath' then return nil end
  return pandoc.RawInline('latex', '\\[\\adjustbox{max width=\\linewidth}{$\\displaystyle ' ..
    el.text .. '$}\\]')
end
return {{Table = Table},
        {Header = Header, Div = Div, CodeBlock = CodeBlock, Str = Str, Code = Code, Math = Math}}

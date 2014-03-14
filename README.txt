TODO: There must be a way to file base name in a rule (to force #include "my_header.h" on top)

=== match options (separated by comma)

integer - priority; greater - higher; default: 0; negative values are possible; conflict on the same priority is an error

do-group        - group all matched items [default]
do-group-replace- group all matched items, replace each line with expression from next rule line, only with {match-line}
do-skip         - leave line as is
do-replace      - replace line with expression from next rule line, only with {match-line}
do-remove       - delete line
do-forbid       - exit with error if specified line was encountered
do-check-match  - exit with error if specified line was not matched by other rules (like {do-forbid, -1000000})

match-line      - match whole line [default]
match-substring - match substring
match-ign-tr-ws - match whole line, but ignore trailing whitespace

case-sens       - case sensitive match
case-insens     - case insensitive match

  only for {do-group...}:
sort-none       - keep lines order [default]
sort-smart      - sort lines using version sort (e.g. "A1", "A2", "A10")
sort-alphabetic - sort lines alphabetically (e.g. "A1", "A10", "A2")

  only for {do-group...} and {order-keep}:
vs-rm           - remove blank likes inside group
vs-keep         - keep blank likes inside group; on line removal leave maximum blank lines form one side
vs-keep-all     - keep all blank likes inside group
vs-squeeze      - collapse all vertical space to one line

  only for {do-group...}:
dup-rm-ign-ws   - remove lines which differ only in whitespace
dup-rm-exact    - remove exact duplicates [default]
dup-keep        - keep duplicates


=== special commands

blank           - add vertical space (single blank line)
eat-blank       - eat vertical space (can be only first or last item)
#               - comment



??? ideas

add option aliases

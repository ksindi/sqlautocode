import fnmatch, os, re, sys
import config


_defaultencoding = sys.getdefaultencoding()
_python_identifier_re = re.compile(r'^[a-z_][a-z0-9_]*$', re.I)

def emit(*lines):
    """Emit one or more output strings."""

    for line in lines:
        if not line:
            config.out.write(os.linesep)
        else:
            if isinstance(line, unicode):
                encoding = 'utf-8'
                if getattr(config, 'options', None):
                    encoding = config.options.encoding
                line = line.encode(encoding)
            config.out.write(line)
            if line[-1] != '\n':
                config.out.write(os.linesep)

def is_python_identifier(string):
    """True if string is a valid Python identifier."""

    # unicode-ok.
    return _python_identifier_re.match(string)

def as_out_str(obj):
    """Like str(), but convert unicode to configured encoding."""

    if isinstance(obj, unicode):
        encoding = 'utf-8'
        if getattr(config, 'options', None):
            encoding = config.options.encoding
        return obj.encode(encoding)
    elif not isinstance(obj, str):
        return str(obj)
    else:
        return obj

def as_sys_str(obj, escape='backslashreplace'):
    """Like str(), but safely convert unicode to the system encoding."""

    if isinstance(obj, unicode):
        return obj.encode(_defaultencoding, escape)
    elif not isinstance(obj, str):
        return str(obj)
    else:
        return obj

def unique(iterable):
    seen = set()
    for item in iterable:
        if item not in seen:
            seen.add(item)
            yield item

def glob_intersection(collection, subset):
    """Return elements of subset in collection, with glob support.

    collection
      A collection of strings, need not be a set.
    subset
      Any iterable of strings.

    Items in the subset may be plain strings, "quoted strings" or
    strings with*glob? characters.  Quoted strings are not globbed.
    """

    found, missing, unmatched = [], [], []
    for identifier in unique(subset):
        if identifier[0] == '"':
            name = identifier[1:-1]
            if name in collection:
                found.append(name)
            else:
                missing.append(name)
        elif '*' not in identifier:
            if identifier in collection:
                found.append(identifier)
            else:
                missing.append(identifier)
        else:
            globbed = fnmatch.filter(collection, identifier)
            if globbed:
                found.extend(globbed)
            else:
                unmatched.append(identifier)

    # ordered sets sure would be nice.
    return list(unique(found)), missing, unmatched

# lifted from http://www.daniweb.com/forums/thread70647.html
# (pattern, search, replace) regex english plural rules tuple
plural_rule_tuple = (
('[ml]ouse$', '([ml])ouse$', '\\1ice'),
('child$', 'child$', 'children'),
('booth$', 'booth$', 'booths'),
('foot$', 'foot$', 'feet'),
('ooth$', 'ooth$', 'eeth'),
('l[eo]af$', 'l([eo])af$', 'l\\1aves'),
('sis$', 'sis$', 'ses'),
('man$', 'man$', 'men'),
('ife$', 'ife$', 'ives'),
('eau$', 'eau$', 'eaux'),
('lf$', 'lf$', 'lves'),
('[xz]$', '$', 'es'),
('[s]$', '$', ''),
('[^aeioudgkprt]h$', '$', 'es'),
('(qu|[^aeiou])y$', 'y$', 'ies'),
('$', '$', 's')
)

singular_rule_tuple = (
('[ml]ouse$', '([ml])ouse$', '\\1ice'),
('children$', 'children$', 'child'),
('feet$',     'fee$', 'foot'),
('eeth$',     'eeth$', 'ooth'),
('l[eo]aves', 'l([eo])af$', 'l\\1af$'),
('ses$',      'ses$', 's'),
('men$',      'men$', 'man'),
('ives$',     'ives$', 'ife'),
('eaux$',     'eaux$', 'eau'),
('lves$',     'lves$', 'lf'),
#('[xz]$', '$', 'es'), not sure how to unplural this one
#('[s]$', '$', ''),
('pies$' ,    'pies$', 'pie'),
('ovies$' ,     'ovies$', 'ovie'),
('ies$' ,     'ies$', 'y'),
('xes$' ,     'xes$', 'x'),
#('(qu|[^aeiou])y$', 'y$', 'ies'),
('s$',        's$', '')
)

def regex_rules(rules):
    for line in rules:
        pattern, search, replace = line
        yield lambda word: re.search(pattern, word) and re.sub(search, replace, word)

plural_rules = regex_rules(plural_rule_tuple)

def plural(noun):
    for rule in regex_rules(plural_rule_tuple):
        result = rule(noun)
        if result:
            return result
    return noun

def singular(noun):
    for rule in regex_rules(singular_rule_tuple):
        result = rule(noun)
        if result:
            return result
    return noun

def name2label(name, schema=None):
    """
    Convert a column name to a Human Readable name.
    borrowed from old TG fastdata code
    """
    # Create label from the name:
    #   1) Convert _ to Nothing
    #   2) Convert CamelCase to Camel Case
    #   3) Upcase first character of Each Word
    # Note: I *think* it would be thread-safe to
    #       memoize this thing.
    if schema:
        if name.startswith(schema+'.'):
            name = '.'.join(name.split('.')[1:])
    label = str(''.join([s.capitalize() for s in
               re.findall(r'([A-Z][a-z0-9]+|[a-z0-9]+|[A-Z0-9]+)', name)]))
    return label
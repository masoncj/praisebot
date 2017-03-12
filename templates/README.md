# Praisebot templates



Praisebot templates allow to customize the printed appearance of a praise sticker.

A praisebot template is a handlebars template producing an SVG file.  

## Naming

The name of the template (minus the `svg` extension) is also the word used to trigger the invocation of the template in an
instant message. Therefore, choose a name that is a memorable verb, such as "thank", "highfive", or "ship".

## Variables

* `recipient` - The recipient of the praise, either an `@` prefixed username, or a `#`
 prefixed channel.
* `recipient_name` - The full name of the channel or user who sent the praise.
* `sender` - The username of the user who sent the praise.
* `sender_name` - The full name of the user who sent the praise.
* `bot_user` - The username of this praise bot.
* `bot_user_name` - The full name of this praise bot.

* `message` - The complete text of message of praise, including the intial word "for", 
if present.
* `text` - The message text without any "for".
* `template_name` - The name (not path) of the template being rendered.
* `date` - The human-readable date and time at which the praise was initiated.
* `date_numeric` - a sortable datetime string of the format 20170311_0927 for use, eg, in filenames

Additional variables can be passed in the chat message by using the `with` syntax.

## Template Title and Filename

Templates also contain two additional XML elements that are used to generate a textual
title and filename for the praise.  The `title` is used where a plain-text representation
of the praise is need, for instance in slack message.  The `filename` is used to name
the media files (eg PNG or PDF) uploaded to slack or a printer. The filename should contain a
datetime code to uniquely identify it but should *not* contain a file extension (eg `png`).

For example:  

```xml
<title>{{sender}} thanked {{recipient}}</title>
<metadata>
  <filename>{{sender}}_thanked_{{recipient}}_{{date_numeric}}</filename>
```

## Helpers

### `wrap`

`wrap`: performs simple text wrapping on one or more template variables. The wrap command
 repeats the contained template content for each wrapped line, substituting `x`, `y`, 
 and `text`.   Takes two 
  additional keyword arguments that control how wrapping is performed.
  * `width_chars` - the length of the line in unicode characters at which to wrap.
  * `height_pixels` - the y-offset to add for each line.

Example:

```handlebars
{{#wrap message width_chars="30" height_pixels="22" }}
    <tspan x="{{x}}" y="{{y}}" class="bold">{{text}}</tspan>
{{/wrap}}
```

## Reserved template names:

* `help`
* `list`

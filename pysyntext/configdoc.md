# Syntax for `config.json`

To initialize class just type properties and values for constructor using the following format:  
`"property": value`

You can also pass obtained object instead of primitive. To do so, assign the property with the following dictionary:
```json
{
	"object": "type of object",
	"name": "address or name of object to initialize"
}
```

## Supporting type of objects

### `class`

In order to pass the initialized class, try the following syntax:

`{"object": "class", "name": "address to your class"}`

Address will be interpreted respectively to `libs` folder as the root. For example: `gc.GC` means `GC` class from `libs/gc`.  
You can also pass additional properties for constructor of that class in `props` field. Otherwise, the defaults from this file will be used.

### `function`

You can pass the function with the following format:

`{"object": "function", "name": "address to your function"}`

Here address will be interpreted respectively to `libs` path as root. For example, `ud.mte.MTEParser.parse` mean the following function:

`libs.ud.mte` - class `MTEParser` - method `parse`.

### `sysvar`

Using the following syntax:

`{"object": "sysvar", "name": "SYNTEXTDBPWD"}`

you can get environment variable named `SYNTEXTDBPWD`.
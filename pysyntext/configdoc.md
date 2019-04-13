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

Every class should have `$location` property which is pointer to package where to load class from. Example: ```"A": {"$location": "B.C"}``` is equivalent to `from B.C import A`.

## Addressing objects

When initializing classes (see the paragraph above) you may pass objects you want by their addresses. Correct address has the following structure:
`(packagename),(optionally: classname),(optionally: functionname)`
Thus, `libs.morphology,MorphologyRecognizer,selectFirst` returns method `selectFirst` on class `MorphologyRecognizer` of package `libs.morphology`.

## Supporting type of objects

### `class`

In order to pass the initialized class, try the following syntax:

`{"object": "class", "name": "address to your class"}`

You can also pass additional properties for constructor of that class in `props` field. Otherwise, the defaults from this file will be used.

### `function`

You can pass the function with the following format:

`{"object": "function", "name": "address to your function"}`

### `sysvar`

Using the following syntax:

`{"object": "sysvar", "name": "SYNTEXTDBPWD"}`

you can get environment variable named `SYNTEXTDBPWD`.

### `fp`

File pointer can be passed with the following syntax:

`{
	"object": "fp",
	"address": "address to your file", 
	"mode": "python-like mode of the opening of the file"
}`

This will return file opened by `open()` function.

### `jsonfp`

Following syntax will take given file, encode as JSON and pass the result to a class:

`{"object": "fp", "address": "address to your file"}`

### `lambda`

Sometimes class should be initialized with some non-built-in object. In order to define it, you should pass lambda function to `inited()` method:
```python
Predefinator.inited(
	your_parameter=lambda obj: your_function(obj)
)
```
Configs should look like this:
`"your_parameter": {
	"object": "lambda", "data": "data to initialize with",
	"name": "name of variable where this lambda will be defined"
	}`
Then class will be created in the following way:
```python
return Your_Class(
	your_parameter=kwargs["your_parameter"]("data to initialize with")
)
```

### `defined`

If passed, this parameter will be obtained from kwargs, passed to `inited` function. Syntax is the following:

`{"object": "defined", "name": "name of variable where this prop is defined"}`

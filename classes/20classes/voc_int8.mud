[basic]
type = awnn
param =./voc_int8.param
bin =./voc_int8.bin

[inputs]
input0 = 224,224,3,127.5, 127.5, 127.5,0.0078125, 0.0078125, 0.0078125

[outputs]
output0 = 7,7,125

[extra]
outputs_scale =
inputs_scale=

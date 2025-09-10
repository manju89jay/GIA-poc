typedef struct {
    int value;
    int count;
} SampleInner;

typedef struct {
    SampleInner inner;
    int flag;
} ExamplePort;

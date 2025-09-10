typedef struct {
    int value;
    int total;
} SampleInner;

typedef struct {
    SampleInner inner;
    int flag;
    bool active;
} ExamplePort;

import beaker as bk
import pyteal as pt

from beaker import client, localnet
from beaker.lib.storage import BoxMapping


class TypeOne(pt.abi.NamedTuple):
    score: pt.abi.Field[pt.abi.Uint64]


class TypeTwo(pt.abi.NamedTuple):
    lmao: pt.abi.Field[pt.abi.String]
    foo: pt.abi.Field[pt.abi.Address]
    tt_score: pt.abi.Field[pt.abi.Uint64]
    to: pt.abi.Field[TypeOne]


class State:
    my_box_one = BoxMapping(
        key_type=pt.abi.Uint64,
        value_type=TypeOne
    )
    my_box_two = BoxMapping(
        key_type=pt.abi.String,
        value_type=TypeTwo
    )


app = bk.Application("App", state=State())


@app.external
def setup1(score: pt.abi.Uint64, tracker_id: pt.abi.Uint64) -> pt.Expr:
    return pt.Seq(
        (to := TypeOne()).set(score),
        app.state.my_box_one[pt.Itob(tracker_id.get())].set(to)
    )


@app.external
def setup2(lmao: pt.abi.String, tracker_id: pt.abi.Uint64) -> pt.Expr:
    return pt.Seq(
        (to := TypeOne()).decode(app.state.my_box_one[pt.Itob(tracker_id.get())].get()),
        (foo := pt.abi.Address()).set(pt.Txn.sender()),
        (tt_score := pt.abi.Uint64()).set(10),
        (tt := TypeTwo()).set(lmao, foo, tt_score, to),
        app.state.my_box_two[pt.Itob(tracker_id.get())].set(tt)
    )


@app.external
def read_box1(tracker_id: pt.abi.Uint64, *, output: TypeOne) -> pt.Expr:
    return app.state.my_box_one[pt.Itob(tracker_id.get())].store_into(output)


@app.external
def read_box2(tracker_id: pt.abi.Uint64, *, output: TypeTwo) -> pt.Expr:
    return app.state.my_box_one[pt.Itob(tracker_id.get())].store_into(output)


accts = localnet.get_accounts()
admin_acct = accts[0]
project_owner = accts[1]

algod_client = localnet.get_algod_client()

app_client = client.ApplicationClient(
    client=algod_client,
    app=app,
    sender=admin_acct.address,
    signer=admin_acct.signer,
)
app_id, app_addr, _ = app_client.create()

app_client.fund(10_000_000)

tracker_id = 1
app_client.call(
    setup1,
    score=5,
    tracker_id=tracker_id,
    boxes=[(app_id, tracker_id.to_bytes(8, "big"))]
)
result = app_client.call(
    read_box1,
    tracker_id=tracker_id,
    boxes=[(app_id, tracker_id.to_bytes(8, "big"))]
)
print(f"Result of first box: {result.return_value}")

tracker_id = 1
app_client.call(
    setup2,
    lmao="haha",
    tracker_id=tracker_id,
    boxes=[(app_id, tracker_id.to_bytes(8, "big"))]
)
result = app_client.call(
    read_box2,
    tracker_id=tracker_id,
    boxes=[(app_id, tracker_id.to_bytes(8, "big"))]
)
print(f"Result of second box: {result.return_value}")

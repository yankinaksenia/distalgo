----------------------------- MODULE program -----------------------------
EXTENDS Integers, Sequences, TLC
CONSTANT N (* amount of client processes*)
(*
--algorithm translate_dist {
  variables
    (* communication network, representing messages in transit *)
    channel = [<<snd,dst>> \in ProcSet \X ProcSet |-> <<>>],
    (* receive history per process, stores pairs of received messages and sender *)
    rcv_history = [ proc \in ProcSet |-> <<>> ];
    sent_history = [ proc \in ProcSet |-> <<>> ];

  define {
  (* check if process proc has some message of the given kind, sent from
     some process in snds, in its receive history *)
   some_received(proc, kind, snds) ==
     LET rcvd == rcv_history[proc]
     IN  \E i \in 1 .. Len(rcvd) :
            /\ rcvd[i][1] = kind
            /\ rcvd[i][2] \in snds


   some_sent(proc, kind, rcvs) ==
     LET sent_h == sent_history[proc]
     IN  \E i \in 1 .. Len(sent_h) :
            /\ sent_h[i][1] = kind
            /\ sent_h[i][2] \in rcvs
  } \* end define

(*---------------------------------macro_for_functions----------------------------------------*)

macro handle_Ping_0(msg, snd) {
    \* BODGE : direct access to local variables of the process!!
    ${BODY_PLACEHOLDER}
    }
  }

macro handle_Pong_0(msg, snd) {
    \* BODGE : direct access to local variables of the process!!
    ${BODY_PLACEHOLDER}
    }
  }

macro send(msg,sender, receiver)
{
    channel[sender,receiver] := Append(@, msg);
    sent_history[sender] := Append(@, <<msg, receiver>>);
}

(*---------------------------------procedures----------------------------------------*)

procedure receive_message_Ping()
    variables sndr, mesg;
  {
rcv_msg:
    while (\E snd \in ProcSet : Len(channel[snd,0]) > 0) {
      with (snd \in {proc \in ProcSet : Len(channel[proc,0]) > 0}) {
        sndr := snd;
        mesg := Head(channel[snd,0])
      } ;
      \* move the message to the receive history
      rcv_history[0] := Append(@, <<mesg, sndr>>);
      \* if there is a handler for the message, execute it

        if (mesg[1] = "Pong") {
	handle_Ping_0(mesg, sndr)
}
      } ;
do_rcv: \* this label is not really necessary, but we add it to be on the safe side
      \* remove the message from the channel
      channel[sndr,0] := Tail(@)
    }; \* end while
    return
  } \* end procedure


 
 



procedure receive_message_Pong()
    variables sndr, mesg;
  {
rcv_msg:
    while (\E snd \in ProcSet : Len(channel[snd,1]) > 0) {
      with (snd \in {proc \in ProcSet : Len(channel[proc,1]) > 0}) {
        sndr := snd;
        mesg := Head(channel[snd,1])
      } ;
      \* move the message to the receive history
      rcv_history[1] := Append(@, <<mesg, sndr>>);
      \* if there is a handler for the message, execute it

        if (mesg[1] = "Ping") {
	handle_Pong_0(mesg, sndr)
}
      } ;
do_rcv: \* this label is not really necessary, but we add it to be on the safe side
      \* remove the message from the channel
      channel[sndr,1] := Tail(@)
    }; \* end while
    return
  } \* end procedure


 
 


(*---------------------------------processes----------------------------------------*)

process (Ping = 0)
	variables
msg_back = "None",
process = "y",
{
    
send(<<"Ping", msg_in, incr>>, self, p)
print("wait in ping")
call receive_messages_Ping()
print(msg_back)
}
process (Pong = 1)
	variables
msg_out = "None",
process = "y",
{
    
print("Waiting")
call receive_messages_Pong()
print(incr)
}


} \* end algorithm
*)


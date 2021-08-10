from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only
from datetime import datetime
import sys

from models import Base, Order, Log
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

@app.before_request
def create_session():
    g.session = scoped_session(DBSession)

@app.teardown_appcontext
def shutdown_session(response_or_exc):
    sys.stdout.flush()
    g.session.commit()
    g.session.remove()


""" Suggested helper methods """

def check_sig(payload,sig):
    pass

def fill_order(order,txes=[]):
    pass
  
def log_message(d):
    # Takes input dictionary d and writes it to the Log table
    # Hint: use json.dumps or str() to get it in a nice string form
    msg_dict = d['payload']
    log_obj = Log(message = json.dumps(msg_dict))

""" End of helper methods """



@app.route('/trade', methods=['POST'])
def trade():
    print("In trade endpoint")
    if request.method == "POST":
        content = request.get_json(silent=True)
        print( f"content = {json.dumps(content)}" )
        columns = [ "sender_pk", "receiver_pk", "buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform" ]
        fields = [ "sig", "payload" ]

        for field in fields:
            if not field in content.keys():
                print( f"{field} not received by Trade" )
                print( json.dumps(content) )
                log_message(content)
                return jsonify( False )
        
        for column in columns:
            if not column in content['payload'].keys():
                print( f"{column} not received by Trade" )
                print( json.dumps(content) )
                log_message(content)
                return jsonify( False )
            
        #Your code here
        #Note that you can access the database session using g.session
        platform = content['payload']['platform']
        msg_dict = content['payload']
        message = json.dumps(msg_dict)
        pk = content['payload']['sender_pk']
        sig = content["sig"]
        verify = False
        
        if platform == "Ethereum":
          eth_encoded_msg = eth_account.messages.encode_defunct(text=message)

          pk2 = eth_account.Account.recover_message(eth_encoded_msg,signature=sig)

          if pk == pk2:
            print( "Eth sig verifies!" )
            verify = True

          else:
            print( "Eth sig fails verification!" )
            verify = False


        elif platform == "Algorand":

          if algosdk.util.verify_bytes(message.encode('utf-8'),sig,pk):
            print( "Algo sig verifies!" )
            verify = True
          else:
            print( "Algo sig verification failed!" )
            verify = False
            
        if verify == True:
          order = Order( sender_pk=msg_dict['sender_pk'],receiver_pk=msg_dict['receiver_pk'], buy_currency=msg_dict['buy_currency'], sell_currency=msg_dict['sell_currency'], buy_amount=msg_dict['buy_amount'], sell_amount=msg_dict['sell_amount'], signature = content['sig'] )
          g.session.add(order)
          g.session.commit();
          
          return jsonify(True)
          
        else:
          log_message(content)
          return jsonify(False)
        # TODO: Check the signature
        
        # TODO: Add the order to the database
        
        # TODO: Fill the order
        
        # TODO: Be sure to return jsonify(True) or jsonify(False) depending on if the method was successful
        

@app.route('/order_book')
def order_book():
    #Your code here
    #Note that you can access the database session using g.session
    existing = g.session.query(Order).all()
    result = {"data": []}

    for row in existing:
        # timestamp_str = str(row.timestamp)
        result['data'].append({'sender_pk': row.sender_pk,'receiver_pk': row.receiver_pk, 'buy_currency': row.buy_currency, 'sell_currency': row.sell_currency, 'buy_amount': row.buy_amount, 'sell_amount': row.sell_amount,'signature': row.signature})

    return jsonify(result)

if __name__ == '__main__':
    app.run(port='5002')

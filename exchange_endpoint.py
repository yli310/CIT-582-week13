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

def process_order(order):
    #Your code here
    #order = Order( sender_pk=order_dict['sender_pk'],receiver_pk=order_dict['receiver_pk'], buy_currency=order_dict['buy_currency'], sell_currency=order_dict['sell_currency'], buy_amount=order_dict['buy_amount'], sell_amount=order_dict['sell_amount'] )
    g.session.add(order)
    g.session.commit();
    
    buy_curr = order.buy_currency
    sell_curr = order.sell_currency
    buy_am = order.buy_amount
    sell_am = order.sell_amount
    send_pk = order.sender_pk
    receive_pk = order.receiver_pk
    exchange_rate = buy_am/sell_am
    
    existing_orders = g.session.query(Order).filter(Order.filled == None, Order.buy_currency == order.sell_currency,Order.sell_currency == order.buy_currency, Order.sell_amount/Order.buy_amount >= exchange_rate).all()
    if exisiing_order == None:
      return
    #filled
    for existing in existing_orders:
      order.filled = datetime.now()
      existing.filled = datetime.now()
      g.session.commit()
      #counterparty id
      order.counterparty_id = existing.id
      existing.counterparty_id = order.id
      g.session.commit()

      #order can buy more
      if(existing.sell_amount <= buy_am):
        new_buy = buy_am - existing.sell_amount
        new_sell = new_buy / exchange_rate
        #Insert the order
        order_obj = Order( sender_pk=order.sender_pk,receiver_pk=order.receiver_pk, buy_currency=order.buy_currency, sell_currency=order.sell_currency, buy_amount=new_buy, sell_amount=new_sell, creator_id = order.id)
        g.session.add(order_obj)
        g.session.commit()
      elif(existing.sell_amount>buy_am):
        new_sell = existing.sell_amount - buy_am
        new_buy = new_sell * existing.buy_amount/existing.sell_amount
        #Insert the order
        order_obj = Order( sender_pk=existing.sender_pk,receiver_pk=existing.receiver_pk, buy_currency=existing.buy_currency, sell_currency=existing.sell_currency, buy_amount=new_buy, sell_amount=new_sell, creator_id = existing.id)
        g.session.add(order_obj)
        g.session.commit()
      break;
    return


      


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
          
        order = Order( sender_pk=msg_dict['sender_pk'],receiver_pk=msg_dict['receiver_pk'], buy_currency=msg_dict['buy_currency'], sell_currency=msg_dict['sell_currency'], buy_amount=msg_dict['buy_amount'], sell_amount=msg_dict['sell_amount'], signature = content['sig'] )
        process_order(order)  
        if verify == True:
          
          #g.session.add(order)
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

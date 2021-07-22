/*
 * @Author: your name
 * @Date: 2020-05-22 11:55:44
 * @LastEditTime: 2020-05-25 12:46:34
 * @LastEditors: Please set LastEditors
 * @Description: In User Settings Edit
 * @FilePath: /kungfu/cli/src/assets/scripts/actions/tradingDataActions.ts
 */ 
import { map } from 'rxjs/operators';
import { encodeKungfuLocation } from '__io/kungfu/kungfuUtils';
import { ensureLedgerData } from '__gUtils/busiUtils';

export const tradingDataObservale = (type: string, processId: string) => {
    //has to be here, because of the watcher build needed to be after prompt select
    const { buildKungfuDataByAppPipe } = require('__io/kungfu/tradingData');
    const { watcher, 
        transformTradingItemListToData, 
        transformAssetItemListToData, 
        getOrdersBySourceDestInstrumentId, 
        getTradesBySourceDestInstrumentId, 
        getOrderStatByDest, 
        transformOrderStatListToData, 
        dealPos, 
        dealAsset, 
        dealOrderStat 
    } = require('__io/kungfu/watcher');

    const sourceDest = getLocationUID(watcher, type, processId) 
    return buildKungfuDataByAppPipe().pipe(
        map(() => {
            const ledgerData = watcher.ledger;

            const positions = ensureLedgerData(ledgerData.Position).map((item: PosOriginData) => dealPos(item));
            const assets = ensureLedgerData(ledgerData.Asset).map((item: AssetOriginData) => dealAsset(item));

            if (type === 'account') {
                const orders = getOrdersBySourceDestInstrumentId(ledgerData.Order, 'source', sourceDest);
                const trades = getTradesBySourceDestInstrumentId(ledgerData.Trade, 'source', sourceDest);
                const orderStat = getOrderStatByDest(ledgerData.OrderStat, 'dest', sourceDest);
                const orderStatResolved = transformOrderStatListToData(orderStat);  
                const ordersResolved = dealOrdersFromWatcher(orders, orderStatResolved, dealOrderStat);
                const tradesResolved = dealTradesFromWathcer(trades, orderStatResolved, dealOrderStat);
                const positionsResolved = transformTradingItemListToData(positions, 'account')[processId] || [];
                const assetsResolved = transformAssetItemListToData(assets, 'account')[processId] || [];

                return {
                    orders: ordersResolved,
                    trades: tradesResolved,
                    positions: dealPosFromWatcher(positionsResolved),
                    assets: assetsResolved
                }

            } else if (type === 'strategy') {
                const orders = getOrdersBySourceDestInstrumentId(ledgerData.Order, 'dest', sourceDest);
                const trades = getTradesBySourceDestInstrumentId(ledgerData.Trade, 'dest', sourceDest);
                const orderStat = getOrderStatByDest(ledgerData.OrderStat);
                const orderStatResolved = transformOrderStatListToData(orderStat);  
                const ordersResolved = dealOrdersFromWatcher(orders, orderStatResolved, dealOrderStat);
                const tradesResolved = dealTradesFromWathcer(trades, orderStatResolved, dealOrderStat);
                const positionsResolved = transformTradingItemListToData(positions, 'strategy')[processId] || [];
                const assetsResolved = transformAssetItemListToData(assets, 'strategy')[processId] || [];

                return {
                    orders: ordersResolved,
                    trades: tradesResolved,
                    positions: positionsResolved,
                    assets: assetsResolved
                }

            } else {

                return {
                    orders: [],
                    trades: [],
                    positions: {},
                    assets: []
                }
            }
        })
    )
}


function getLocationUID (watcher: any, type: string, currentId: string) {
    if (type === 'account') {
        return watcher.getLocationUID(encodeKungfuLocation(currentId, 'td'));
    } else if (type === 'strategy') {
        return watcher.getLocationUID(encodeKungfuLocation(currentId, 'strategy'));
    } else {
        console.error('getLocationUID type is not account or strategy')
        return 0
    }
}

function dealOrdersFromWatcher (orders: OrderData[], orderStatOrigin: { [prop: string]: OrderStatOriginData }, dealOrderStat: any) {
    return orders.map((orderData: OrderData) => {
        const latencyData: any = orderStatOrigin[orderData.orderId] || null;
        const orderStat = dealOrderStat(latencyData);
        //@ts-ignore
        const { latencySystem, latencyNetwork } = orderStat
        return {
            ...orderData,
            latencySystem: latencySystem || '',
            latencyNetwork: latencyNetwork || ''
        }

    })
}

function dealTradesFromWathcer (trades: TradeData[], orderStatOrigin: { [prop: string]: OrderStatOriginData }, dealOrderStat: any) {
    return trades.map((tradeData: TradeData) => {
        const latencyData: any = orderStatOrigin[tradeData.orderId] || null;
        const orderStat = dealOrderStat(latencyData);
        //@ts-ignore
        const latencyTrade = orderStat.latencyTrade || '';

        return {
            ...tradeData,
            latencyTrade

        }
    })
}

function dealPosFromWatcher (positions: PosData[]): { [propName: string]: PosData } {
    let positionDataByKey: { [propName: string]: PosData } = {};
    
    positions
    .sort((pos1: PosData, pos2: PosData) => {
        if (pos1.instrumentId > pos2.instrumentId) {
            return 1
        } else if (pos1.instrumentId < pos2.instrumentId) {
            return -1
        } else {
            return 0
        };
    })
    .kfForEach((item: PosData) => {
        let positionData = item;
        const poskey = positionData.instrumentId + positionData.direction
        positionDataByKey[poskey] = positionData;
    })

    return positionDataByKey
}
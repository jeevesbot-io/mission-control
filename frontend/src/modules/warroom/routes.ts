export default {
  module: {
    id: 'warroom',
    name: 'War Room',
    icon: 'swords',
    navOrder: 5,
  },
  routes: [
    {
      path: '/warroom',
      component: () => import('./WarRoomPage.vue'),
      meta: { title: 'War Room' },
    },
  ],
  overviewWidgets: [
    {
      id: 'warroom-summary',
      component: () => import('./widgets/WarRoomSummary.vue'),
    },
  ],
}
